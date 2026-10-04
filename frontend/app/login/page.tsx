"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const user = await login(email, password);
      router.push(user.onboarding_completed_at ? "/today" : "/onboarding/areas");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <div className="nav">
        <Link className="wordmark" href="/">
          MyCoach
        </Link>
      </div>
      <h1>Welcome back.</h1>
      <p className="lede">Your room is as you left it. Just today.</p>
      <form className="stack" style={{ marginTop: 28, maxWidth: 420 }} onSubmit={onSubmit}>
        <div>
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <p className="muted small">
          <Link href="/forgot-password">Forgot password?</Link>
          {" · "}
          New here? <Link href="/signup">Create a room</Link>
        </p>
      </form>
    </main>
  );
}
