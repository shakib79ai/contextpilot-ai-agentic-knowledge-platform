import Link from "next/link";

export default function HomePage() {
  return (
    <main className="container stack">
      <h1>ContextPilot AI</h1>
      <p className="muted">
        A production-style multi-agent knowledge platform: retrieval-augmented answers, confidence
        scoring, human-in-the-loop review, and continuous context learning.
      </p>
      <div className="panel stack">
        <div>
          <strong>1. <Link href="/login">Log in or register</Link></strong>
          <p className="muted">Create an account, then ask an operator to run <code>scripts/promote_user.py</code> to grant reviewer/admin access if you need the Review Dashboard.</p>
        </div>
        <div>
          <strong>2. <Link href="/documents">Upload documents</Link></strong>
          <p className="muted">Documents are chunked, embedded, and indexed asynchronously by a Celery worker.</p>
        </div>
        <div>
          <strong>3. <Link href="/chat">Ask questions</Link></strong>
          <p className="muted">Every answer is scored for confidence and cited against retrieved source chunks.</p>
        </div>
        <div>
          <strong>4. <Link href="/review">Review escalated answers</Link></strong>
          <p className="muted">Low-confidence answers wait here for a human reviewer instead of reaching users unchecked.</p>
        </div>
      </div>
    </main>
  );
}
