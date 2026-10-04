"use client";

import { FormEvent, Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { resetPassword } from "@/lib/api";

function ResetForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [token, setToken] = useState(params.get("token") || "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await resetPassword(token, password);
      router.push("/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reset password");
    }
  }

  return (
    <form className="card stack" onSubmit={onSubmit}>
      {error ? <p className="error">{error}</p> : null}
      <label>
        Reset token
        <input value={token} onChange={(e) => setToken(e.target.value)} required />
      </label>
      <label>
        New password
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={10}
        />
      </label>
      <button type="submit">Set new password</button>
      <Link className="muted small" href="/login">
        Back to sign in
      </Link>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="shell narrow">
      <Link className="wordmark" href="/">
        MyCoach
      </Link>
      <p className="eyebrow">Account</p>
      <h1>Choose a new password</h1>
      <Suspense fallback={<p className="muted">Loading…</p>}>
        <ResetForm />
      </Suspense>
    </main>
  );
}
