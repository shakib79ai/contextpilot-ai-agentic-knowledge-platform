"use client";

import { useEffect, useState } from "react";
import { api, ReviewTask } from "@/lib/api";

export default function ReviewPage() {
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [correction, setCorrection] = useState("");

  async function refresh() {
    try {
      setTasks(await api.listReviewTasks());
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function claim(id: string) {
    try {
      await api.claimReviewTask(id);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function resolve(id: string, decision: "approve" | "edit" | "reject") {
    try {
      await api.resolveReviewTask(id, decision, decision === "edit" ? correction : undefined);
      setEditingId(null);
      setCorrection("");
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <main className="container stack">
      <h2>Human Review Queue</h2>
      <p className="muted">
        Low-confidence and escalated answers land here instead of reaching the end user unchecked. Requires a
        reviewer or admin account.
      </p>
      {error && <div className="error">{error}</div>}

      <div className="stack">
        {tasks.map((task) => (
          <div key={task.id} className="panel stack">
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <span className={`badge ${task.status}`}>{task.status}</span>
              <span className="muted">priority: {task.priority}</span>
              <span className="muted">{new Date(task.created_at).toLocaleString()}</span>
            </div>
            {task.reason && <p className="muted">{task.reason}</p>}

            <div style={{ display: "flex", gap: "0.5rem" }}>
              {task.status === "pending" && <button className="secondary" onClick={() => claim(task.id)}>Claim</button>}
              <button onClick={() => resolve(task.id, "approve")}>Approve</button>
              <button className="secondary" onClick={() => setEditingId(task.id)}>Edit</button>
              <button className="danger" onClick={() => resolve(task.id, "reject")}>Reject</button>
            </div>

            {editingId === task.id && (
              <div className="stack">
                <textarea
                  rows={4}
                  placeholder="Corrected answer content"
                  value={correction}
                  onChange={(e) => setCorrection(e.target.value)}
                />
                <button onClick={() => resolve(task.id, "edit")}>Submit correction</button>
              </div>
            )}
          </div>
        ))}
        {tasks.length === 0 && <p className="muted">No review tasks right now.</p>}
      </div>
    </main>
  );
}
