"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register({
        email,
        password,
        display_name: displayName,
        timezone,
      });
      router.push("/onboarding/areas");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create account");
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
      <h1>Begin.</h1>
      <p className="lede">A few details, then choose what you want to grow.</p>
      <form className="stack" style={{ marginTop: 28, maxWidth: 420 }} onSubmit={onSubmit}>
        <div>
          <label htmlFor="name">What should we call you?</label>
          <input id="name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="password">Password (10+ characters)</label>
          <input
            id="password"
            type="password"
            minLength={10}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit" disabled={busy}>
          {busy ? "Creating…" : "Create room"}
        </button>
        <p className="muted small">
          Already have one? <Link href="/login">Sign in</Link>
        </p>
      </form>
    </main>
  );
}
