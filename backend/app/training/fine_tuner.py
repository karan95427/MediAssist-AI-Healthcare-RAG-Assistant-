from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from peft import LoraConfig, TaskType, get_peft_model
from torch.utils.data import Dataset, random_split
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, default_data_collator

from app.config.settings import get_settings
from app.training.dataset_builder import FineTuningDatasetBuilder, TrainingExample

settings = get_settings()


SYSTEM_PROMPT = (
    "You are MediAssist AI, a safe healthcare assistant. "
    "Give clear, professional, patient-friendly healthcare information. "
    "Do not diagnose diseases, prescribe medication, invent clinical facts, or replace a qualified clinician."
)


class CausalChatTrainingDataset(Dataset):
    def __init__(self, examples: list[TrainingExample], tokenizer: Any, max_length: int = 1024) -> None:
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> dict[str, list[int]]:
        example = self.examples[index]
        prompt_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": example.prompt},
        ]
        full_messages = [
            *prompt_messages,
            {"role": "assistant", "content": example.response},
        ]

        prompt_text = self.tokenizer.apply_chat_template(prompt_messages, tokenize=False, add_generation_prompt=True)
        full_text = self.tokenizer.apply_chat_template(full_messages, tokenize=False, add_generation_prompt=False)

        tokenized = self.tokenizer(
            full_text,
            max_length=self.max_length,
            truncation=True,
            padding="max_length",
        )
        prompt_ids = self.tokenizer(
            prompt_text,
            max_length=self.max_length,
            truncation=True,
            add_special_tokens=False,
        )["input_ids"]

        labels = list(tokenized["input_ids"])
        prompt_length = min(len(prompt_ids), len(labels))
        for idx in range(prompt_length):
            labels[idx] = -100
        labels = [token_id if attention else -100 for token_id, attention in zip(labels, tokenized["attention_mask"])]

        return {
            "input_ids": tokenized["input_ids"],
            "attention_mask": tokenized["attention_mask"],
            "labels": labels,
        }


@dataclass(slots=True)
class FineTuningConfig:
    base_model_name: str = settings.local_base_model_name
    output_dir: str = settings.fine_tuned_model_dir
    epochs: int = 1
    train_batch_size: int = 1
    eval_batch_size: int = 1
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    validation_split: float = 0.05
    seed: int = 42
    max_examples: int | None = None
    max_length: int = 1024
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05


class FineTuningTrainer:
    def __init__(self, config: FineTuningConfig | None = None) -> None:
        self.config = config or FineTuningConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def train(self) -> Path:
        builder = FineTuningDatasetBuilder()
        examples = builder.build_examples()
        examples = self._limit_examples_by_source(examples, self.config.max_examples)
        if len(examples) < 10:
            raise ValueError("Not enough training examples were found in the dataset directory.")

        tokenizer = AutoTokenizer.from_pretrained(self.config.base_model_name, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"

        use_cuda = torch.cuda.is_available()
        model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model_name,
            torch_dtype=torch.float16 if use_cuda else torch.float32,
            device_map="auto" if use_cuda else None,
            trust_remote_code=True,
        )
        model.config.use_cache = False
        if hasattr(model, "gradient_checkpointing_enable"):
            model.gradient_checkpointing_enable()

        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            bias="none",
        )
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

        dataset = CausalChatTrainingDataset(examples, tokenizer, max_length=self.config.max_length)
        eval_size = max(1, int(len(dataset) * self.config.validation_split))
        train_size = len(dataset) - eval_size
        train_dataset, eval_dataset = random_split(
            dataset,
            [train_size, eval_size],
            generator=torch.Generator().manual_seed(self.config.seed),
        )

        args = TrainingArguments(
            output_dir=str(self.output_dir),
            do_train=True,
            do_eval=True,
            num_train_epochs=self.config.epochs,
            per_device_train_batch_size=self.config.train_batch_size,
            per_device_eval_batch_size=self.config.eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            eval_strategy="epoch",
            save_strategy="epoch",
            logging_steps=25,
            load_best_model_at_end=False,
            report_to=[],
            seed=self.config.seed,
            remove_unused_columns=False,
            fp16=use_cuda,
            dataloader_pin_memory=use_cuda,
            optim="adamw_torch",
        )

        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=default_data_collator,
            tokenizer=tokenizer,
        )
        trainer.train()
        model.save_pretrained(str(self.output_dir))
        tokenizer.save_pretrained(str(self.output_dir))
        return self.output_dir

    @staticmethod
    def _limit_examples_by_source(examples: list[TrainingExample], limit: int | None) -> list[TrainingExample]:
        if limit is None or len(examples) <= limit:
            return examples

        source_order: list[str] = []
        buckets: dict[str, deque[TrainingExample]] = {}
        for example in examples:
            if example.source not in buckets:
                buckets[example.source] = deque()
                source_order.append(example.source)
            buckets[example.source].append(example)

        selected: list[TrainingExample] = []
        while len(selected) < limit:
            added_this_round = False
            for source in source_order:
                bucket = buckets[source]
                if not bucket:
                    continue
                selected.append(bucket.popleft())
                added_this_round = True
                if len(selected) >= limit:
                    break
            if not added_this_round:
                break

        return selected
