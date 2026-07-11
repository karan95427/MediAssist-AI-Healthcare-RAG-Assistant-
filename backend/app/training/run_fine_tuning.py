from __future__ import annotations

import argparse

from app.training.fine_tuner import FineTuningConfig, FineTuningTrainer


def main() -> None:
    parser = argparse.ArgumentParser(description="LoRA fine-tune MediAssist AI on healthcare datasets.")
    parser.add_argument("--base-model", type=str, default=None)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--max-examples", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    args = parser.parse_args()

    config = FineTuningConfig(
        epochs=args.epochs,
        max_examples=args.max_examples,
        train_batch_size=args.batch_size,
        eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        max_length=args.max_length,
        learning_rate=args.learning_rate,
    )
    if args.base_model:
        config.base_model_name = args.base_model
    if args.output_dir:
        config.output_dir = args.output_dir

    trainer = FineTuningTrainer(config)
    output_dir = trainer.train()
    print(f"LoRA adapter saved to: {output_dir}")


if __name__ == "__main__":
    main()
