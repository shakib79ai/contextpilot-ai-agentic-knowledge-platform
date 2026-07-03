const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
const TOKEN_KEY = "cp_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      /* ignore parse failure */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export interface Citation {
  chunk_id: string;
  document_id: string | null;
  snippet: string;
  similarity: number;
  source: string;
}

export interface ScoreBreakdown {
  retrieval_quality: number;
  source_relevance: number;
  self_check_score: number;
  historical_feedback_score: number;
  confidence: number;
}

export interface QueryResponse {
  answer_id: string;
  conversation_id: string;
  message_id: string;
  content: string;
  status: string;
  confidence_score: number;
  score_breakdown: ScoreBreakdown;
  citations: Citation[];
  pending_review: boolean;
}

export interface DocumentItem {
  id: string;
  filename: string;
  content_type: string | null;
  status: string;
  error_reason: string | null;
  uploaded_at: string;
  indexed_at: string | null;
}

export interface ReviewTask {
  id: string;
  answer_id: string;
  status: string;
  priority: string;
  reason: string | null;
  created_at: string;
  resolved_at: string | null;
}

export const api = {
  register: (email: string, password: string, full_name?: string) =>
    apiFetch("/auth/register", { method: "POST", body: JSON.stringify({ email, password, full_name }) }),

  login: async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    if (!res.ok) throw new Error(`Login failed: ${res.status}`);
    const data = await res.json();
    setToken(data.access_token);
    return data;
  },

  me: () => apiFetch("/auth/me"),

  ask: (question: string, conversation_id?: string): Promise<QueryResponse> =>
    apiFetch("/query", { method: "POST", body: JSON.stringify({ question, conversation_id }) }),

  uploadDocument: (file: File): Promise<DocumentItem> => {
    const fd = new FormData();
    fd.append("file", file);
    return apiFetch("/documents", { method: "POST", body: fd });
  },

  listDocuments: (): Promise<DocumentItem[]> => apiFetch("/documents"),

  submitFeedback: (answer_id: string, kind: string, comment?: string) =>
    apiFetch("/feedback", { method: "POST", body: JSON.stringify({ answer_id, kind, comment }) }),

  listReviewTasks: (reviewStatus?: string): Promise<ReviewTask[]> =>
    apiFetch(`/review${reviewStatus ? `?review_status=${reviewStatus}` : ""}`),

  claimReviewTask: (id: string): Promise<ReviewTask> => apiFetch(`/review/${id}/claim`, { method: "POST" }),

  resolveReviewTask: (id: string, decision: "approve" | "edit" | "reject", corrected_content?: string, note?: string): Promise<ReviewTask> =>
    apiFetch(`/review/${id}/resolve`, { method: "POST", body: JSON.stringify({ decision, corrected_content, note }) }),

  isLoggedIn: (): boolean => !!getToken(),
  logout: clearToken,
};
