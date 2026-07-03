"use client";

import { useState, type FormEvent } from "react";
import { api, QueryResponse } from "@/lib/api";

interface Turn {
  question: string;
  response: QueryResponse;
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="muted" style={{ display: "flex", justifyContent: "space-between" }}>
        <span>{label}</span>
        <span>{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="score-bar">
        <div style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk(e: FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const response = await api.ask(question, conversationId);
      setConversationId(response.conversation_id);
      setTurns((prev) => [...prev, { question, response }]);
      setQuestion("");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function sendFeedback(answerId: string, kind: "thumbs_up" | "thumbs_down") {
    try {
      await api.submitFeedback(answerId, kind);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <main className="container stack">
      <h2>Ask ContextPilot AI</h2>
      {turns.length === 0 && <p className="muted">No questions yet. Ask something about your uploaded documents.</p>}

      <div className="stack">
        {turns.map((turn, i) => (
          <div key={i} className="panel stack">
            <strong>{turn.question}</strong>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span className={`badge ${turn.response.status}`}>{turn.response.status}</span>
              <span className="muted">confidence {(turn.response.confidence_score * 100).toFixed(0)}%</span>
            </div>
            <p style={{ whiteSpace: "pre-wrap" }}>{turn.response.content}</p>

            {turn.response.citations.length > 0 && (
              <div className="stack">
                <span className="muted">Sources</span>
                {turn.response.citations.map((c, idx) => (
                  <div key={idx} className="citation">
                    [{idx + 1}] {c.snippet} — similarity {(c.similarity * 100).toFixed(0)}% ({c.source})
                  </div>
                ))}
              </div>
            )}

            <details>
              <summary className="muted">Confidence breakdown</summary>
              <div className="stack" style={{ marginTop: "0.5rem" }}>
                <ScoreBar label="Retrieval quality" value={turn.response.score_breakdown.retrieval_quality} />
                <ScoreBar label="Source relevance" value={turn.response.score_breakdown.source_relevance} />
                <ScoreBar label="Self-check" value={turn.response.score_breakdown.self_check_score} />
                <ScoreBar label="Historical feedback" value={turn.response.score_breakdown.historical_feedback_score} />
              </div>
            </details>

            {!turn.response.pending_review && (
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button className="secondary" onClick={() => sendFeedback(turn.response.answer_id, "thumbs_up")}>👍 Helpful</button>
                <button className="secondary" onClick={() => sendFeedback(turn.response.answer_id, "thumbs_down")}>👎 Not helpful</button>
              </div>
            )}
          </div>
        ))}
      </div>

      <form className="panel" onSubmit={handleAsk} style={{ display: "flex", gap: "0.5rem" }}>
        <input
          placeholder="Ask a question about your knowledge base..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" disabled={loading}>{loading ? "Thinking..." : "Ask"}</button>
      </form>
      {error && <div className="error">{error}</div>}
    </main>
  );
}
