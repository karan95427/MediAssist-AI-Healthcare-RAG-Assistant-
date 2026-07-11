import type { AxiosProgressEvent } from "axios";
import api from "./api";

export type SourceCitation = {
  document: string;
  page: number;
  similarity: number;
  snippet: string;
};

export type ChatResponse = {
  answer: string;
  mode: string;
  sources: SourceCitation[];
};

export type ConversationItem = {
  id: number;
  question: string;
  answer: string;
  mode: string;
  sources: SourceCitation[];
  created_at: string;
};

export type UserDocument = {
  id: number;
  filename: string;
  total_pages: number;
  uploaded_at: string;
};

export type UploadResponse = {
  id: number;
  filename: string;
  total_pages: number;
  uploaded_at: string;
  message: string;
};

export async function askQuestion(question: string): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/chat", { question });
  return data;
}

export async function fetchConversationHistory(): Promise<ConversationItem[]> {
  const { data } = await api.get<ConversationItem[]>("/history");
  return data;
}

export async function clearConversationHistory(): Promise<void> {
  await api.delete("/history");
}

export async function fetchDocuments(): Promise<UserDocument[]> {
  const { data } = await api.get<UserDocument[]>("/documents");
  return data;
}

export async function uploadDocument(file: File, onUploadProgress?: (progressEvent: AxiosProgressEvent) => void): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<UploadResponse>("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress,
  });
  return data;
}

export async function deleteDocument(documentId: number): Promise<void> {
  await api.delete(`/document/${documentId}`);
}

