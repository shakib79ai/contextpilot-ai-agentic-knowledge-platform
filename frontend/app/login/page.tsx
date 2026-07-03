"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await api.register(email, password, fullName || undefined);
      }
      await api.login(email, password);
      router.push("/chat");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <div className="panel stack" style={{ maxWidth: 420, margin: "0 auto" }}>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button className={mode === "login" ? "" : "secondary"} onClick={() => setMode("login")}>Log in</button>
          <button className={mode === "register" ? "" : "secondary"} onClick={() => setMode("register")}>Register</button>
        </div>
        <form className="stack" onSubmit={handleSubmit}>
          {mode === "register" && (
            <input placeholder="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          )}
          <input type="email" required placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input type="password" required placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={loading}>
            {loading ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}
          </button>
        </form>
      </div>
    </main>
  );
}
