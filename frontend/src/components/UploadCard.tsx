import { useEffect, useRef, useState } from "react";
import { deleteDocument, fetchDocuments, uploadDocument, type UserDocument } from "../services/assistantService";
import LoadingSpinner from "./LoadingSpinner";

function UploadCard() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [documents, setDocuments] = useState<UserDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setIsLoading(true);
        const data = await fetchDocuments();
        setDocuments(data);
      } catch {
        setError("Unable to load uploaded documents.");
      } finally {
        setIsLoading(false);
      }
    };

    void loadDocuments();
  }, []);

  const handleUpload = async (file: File) => {
    setError(null);
    setUploadProgress(0);
    try {
      const response = await uploadDocument(file, (event) => {
        if (!event.total) {
          return;
        }
        setUploadProgress(Math.round((event.loaded / event.total) * 100));
      });
      setDocuments((current) => [
        {
          id: response.id,
          filename: response.filename,
          total_pages: response.total_pages,
          uploaded_at: response.uploaded_at,
        },
        ...current,
      ]);
    } catch {
      setError("Upload failed. Only PDFs up to 20 MB are supported.");
    } finally {
      setUploadProgress(null);
    }
  };

  const handleDelete = async (documentId: number) => {
    try {
      await deleteDocument(documentId);
      setDocuments((current) => current.filter((document) => document.id !== documentId));
    } catch {
      setError("Unable to delete the selected document.");
    }
  };

  return (
    <section className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
      <div className="rounded-3xl bg-white p-6 shadow-panel">
        <p className="text-sm font-medium text-brand-600">Document Intake</p>
        <h3 className="mt-1 text-lg font-semibold text-slate-900">Upload personal medical PDFs</h3>
        <div
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setIsDragging(false);
            const file = event.dataTransfer.files[0];
            if (file) {
              void handleUpload(file);
            }
          }}
          className={`mt-6 rounded-3xl border border-dashed p-8 text-center ${isDragging ? "border-brand-500 bg-brand-50" : "border-brand-200 bg-brand-50/40"}`}
        >
          <p className="text-sm text-slate-600">Drag and drop a PDF here, or choose a file manually.</p>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="mt-4 rounded-2xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white"
          >
            Select PDF
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) {
                void handleUpload(file);
              }
              event.currentTarget.value = "";
            }}
          />
          <p className="mt-4 text-xs uppercase tracking-[0.16em] text-slate-400">Maximum size 20 MB</p>
          {uploadProgress !== null ? (
            <div className="mt-6">
              <div className="h-3 overflow-hidden rounded-full bg-slate-200">
                <div className="h-full bg-brand-600" style={{ width: `${uploadProgress}%` }} />
              </div>
              <p className="mt-2 text-sm text-slate-500">Uploading {uploadProgress}%</p>
            </div>
          ) : null}
          {error ? <p className="mt-4 text-sm text-rose-600">{error}</p> : null}
        </div>
      </div>

      <div className="rounded-3xl bg-white p-6 shadow-panel">
        <p className="text-sm font-medium text-brand-600">Document Library</p>
        <h3 className="mt-1 text-lg font-semibold text-slate-900">Uploaded reports</h3>
        <div className="mt-6 space-y-3">
          {isLoading ? <LoadingSpinner /> : null}
          {!isLoading && documents.length === 0 ? <p className="text-sm text-slate-500">No documents uploaded yet.</p> : null}
          {documents.map((document) => (
            <div key={document.id} className="flex items-start justify-between gap-4 rounded-2xl border border-slate-200 p-4">
              <div>
                <p className="text-sm font-semibold text-slate-900">{document.filename}</p>
                <p className="mt-2 text-sm text-slate-500">{document.total_pages} pages</p>
                <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-400">
                  {new Date(document.uploaded_at).toLocaleString()}
                </p>
              </div>
              <button
                type="button"
                onClick={() => void handleDelete(document.id)}
                className="rounded-2xl border border-rose-200 px-4 py-2 text-sm font-medium text-rose-600"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default UploadCard;
