"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { forgotPassword } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = await forgotPassword(email);
      setDone(true);
      if (result.reset_token) setToken(result.reset_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    }
  }

  return (
    <main className="shell narrow">
      <Link className="wordmark" href="/">
        MyCoach
      </Link>
      <p className="eyebrow">Account</p>
      <h1>Reset password</h1>
      <p className="lede">We will email a reset link when mail is wired. For now, local/dev returns a token.</p>
      {done ? (
        <div className="card stack">
          <p>If that email has an account, a reset was prepared.</p>
          {token ? (
            <>
              <p className="muted small">Dev token (not shown in production):</p>
              <code className="token-box">{token}</code>
              <Link href={`/reset-password?token=${encodeURIComponent(token)}`}>Continue to set a new password</Link>
            </>
          ) : (
            <Link href="/login">Back to sign in</Link>
          )}
        </div>
      ) : (
        <form className="card stack" onSubmit={onSubmit}>
          {error ? <p className="error">{error}</p> : null}
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <button type="submit">Send reset</button>
          <Link className="muted small" href="/login">
            Back to sign in
          </Link>
        </form>
      )}
    </main>
  );
}
