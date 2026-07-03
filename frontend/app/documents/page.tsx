"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, DocumentItem } from "@/lib/api";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  async function refresh() {
    try {
      setDocuments(await api.listDocuments());
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 4000);
    return () => clearInterval(interval);
  }, []);

  async function handleUpload(e: FormEvent) {
    e.preventDefault();
    const file = fileInput.current?.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadDocument(file);
      if (fileInput.current) fileInput.current.value = "";
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="container stack">
      <h2>Knowledge Base Documents</h2>

      <form className="panel" onSubmit={handleUpload} style={{ display: "flex", gap: "0.5rem" }}>
        <input type="file" ref={fileInput} accept=".pdf,.txt,.md" />
        <button type="submit" disabled={uploading}>{uploading ? "Uploading..." : "Upload"}</button>
      </form>
      {error && <div className="error">{error}</div>}

      <div className="panel">
        <table>
          <thead>
            <tr>
              <th>Filename</th>
              <th>Status</th>
              <th>Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.filename}</td>
                <td>
                  <span className={`badge ${doc.status === "failed" ? "escalated" : doc.status === "indexed" ? "auto_answered" : "pending"}`}>
                    {doc.status}
                  </span>
                  {doc.error_reason && <div className="muted">{doc.error_reason}</div>}
                </td>
                <td className="muted">{new Date(doc.uploaded_at).toLocaleString()}</td>
              </tr>
            ))}
            {documents.length === 0 && (
              <tr>
                <td colSpan={3} className="muted">No documents uploaded yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}
