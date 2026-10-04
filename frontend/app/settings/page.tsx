"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import {
  User,
  changePassword,
  deleteAccount,
  exportAccount,
  me,
  updateMe,
  updatePreferences,
} from "@/lib/api";

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [timezone, setTimezone] = useState("UTC");
  const [weekStartsOn, setWeekStartsOn] = useState(1);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [deletePassword, setDeletePassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    me()
      .then((profile) => {
        setUser(profile);
        setDisplayName(profile.display_name);
        setTimezone(profile.timezone);
        setWeekStartsOn(profile.preferences?.week_starts_on ?? 1);
      })
      .catch(() => {
        setError("Please sign in again.");
        router.push("/login");
      });
  }, [router]);

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const profile = await updateMe({ display_name: displayName, timezone });
      await updatePreferences({ week_starts_on: weekStartsOn });
      setUser(profile);
      setMessage("Saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save");
    }
  }

  async function savePassword(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setMessage("Password updated. Other sessions were signed out.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not change password");
    }
  }

  async function onExport() {
    setError("");
    try {
      const data = await exportAccount();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "mycoach-export.json";
      link.click();
      URL.revokeObjectURL(url);
      setMessage("Export downloaded.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    }
  }

  async function onDelete(event: FormEvent) {
    event.preventDefault();
    if (!window.confirm("Delete your account and all practice history? This cannot be undone.")) return;
    setError("");
    try {
      await deleteAccount(deletePassword);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete account");
    }
  }

  if (!user) {
    return (
      <main className="shell">
        <p className="muted">{error || "Loading settings…"}</p>
      </main>
    );
  }

  return (
    <main className="shell">
      <AppNav active="settings" />
      <p className="eyebrow">Account</p>
      <h1>Settings</h1>
      <p className="lede">Name, timezone, password, export, and delete — nothing invented here.</p>
      {message ? <p className="ok-note">{message}</p> : null}
      {error ? <p className="error">{error}</p> : null}

      <form className="card stack" onSubmit={saveProfile} style={{ marginTop: 24 }}>
        <h2>Profile</h2>
        <label>
          Display name
          <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} required maxLength={120} />
        </label>
        <label>
          Email
          <input value={user.email} disabled />
        </label>
        <label>
          Timezone
          <input value={timezone} onChange={(e) => setTimezone(e.target.value)} required maxLength={64} />
        </label>
        <label>
          Week starts on
          <select value={weekStartsOn} onChange={(e) => setWeekStartsOn(Number(e.target.value))}>
            <option value={1}>Monday</option>
            <option value={0}>Sunday</option>
            <option value={6}>Saturday</option>
          </select>
        </label>
        <button type="submit">Save profile</button>
      </form>

      <form className="card stack" onSubmit={savePassword} style={{ marginTop: 20 }}>
        <h2>Change password</h2>
        <label>
          Current password
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
            minLength={10}
          />
        </label>
        <label>
          New password
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={10}
          />
        </label>
        <button type="submit">Update password</button>
      </form>

      <section className="card stack" style={{ marginTop: 20 }}>
        <h2>Your data</h2>
        <p className="muted small">Download a JSON copy of your areas, practices, and logs.</p>
        <button type="button" className="secondary" onClick={onExport}>
          Export account
        </button>
      </section>

      <form className="card stack danger-card" onSubmit={onDelete} style={{ marginTop: 20 }}>
        <h2>Delete account</h2>
        <p className="muted small">Removes your account and practice history permanently.</p>
        <label>
          Confirm with password
          <input
            type="password"
            value={deletePassword}
            onChange={(e) => setDeletePassword(e.target.value)}
            required
          />
        </label>
        <button type="submit" className="danger">
          Delete account
        </button>
      </form>
    </main>
  );
}
