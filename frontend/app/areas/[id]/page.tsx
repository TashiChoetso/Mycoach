"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AreaChecklist } from "@/components/ChecklistRow";
import { ScoreRing } from "@/components/ScoreRing";
import { AreaBoard, CalendarDay, WeekDay, areaBoard, createFocus } from "@/lib/api";

function weekday(iso: string) {
  return new Date(`${iso}T12:00:00`).toLocaleDateString(undefined, { weekday: "short" });
}

export default function AreaPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [area, setArea] = useState<AreaBoard | null>(null);
  const [week, setWeek] = useState<WeekDay[]>([]);
  const [weekDays, setWeekDays] = useState<CalendarDay[]>([]);
  const [date, setDate] = useState("");
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [kind, setKind] = useState<"check" | "count">("check");
  const [target, setTarget] = useState("8");
  const [unit, setUnit] = useState("min");
  const [busy, setBusy] = useState(false);

  async function load() {
    const payload = await areaBoard(params.id);
    setArea(payload.area);
    setWeek(payload.week);
    setWeekDays(payload.week_days ?? []);
    setDate(payload.date);
  }

  useEffect(() => {
    load().catch(() => {
      setError("Please sign in again.");
      router.push("/login");
    });
  }, [params.id, router]);

  async function addPractice(event: FormEvent) {
    event.preventDefault();
    if (!name.trim() || !area) return;
    setBusy(true);
    setError("");
    try {
      await createFocus({
        user_area_id: area.id,
        name: name.trim(),
        kind,
        target_value: kind === "count" ? Number(target) || 1 : undefined,
        unit: kind === "count" ? unit : undefined,
      });
      setName("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add that");
    } finally {
      setBusy(false);
    }
  }

  if (!area) {
    return (
      <main className="shell wide">
        <p className="muted">{error || "Loading this area…"}</p>
      </main>
    );
  }

  return (
    <main className="shell wide">
      <div className="nav">
        <Link className="wordmark" href="/today">
          MyCoach
        </Link>
        <div className="row">
          <Link className="muted small" href="/progress">
            Progress
          </Link>
          <Link className="muted small" href="/today">
            Back to Today
          </Link>
        </div>
      </div>

      <div className={`area-hero tone-${area.tone}`}>
        <div>
          <p className="eyebrow">Life area</p>
          <h1>{area.name}</h1>
          <p className="lede">You write the list. The score comes from the checks.</p>
          <div className="week" style={{ marginTop: 20 }}>
            {week.map((day) => (
              <div key={day.date} className={`week-cell ${day.date === date ? "today" : ""}`}>
                <span>{weekday(day.date)}</span>
                <strong>{day.score == null ? "—" : day.score}</strong>
              </div>
            ))}
          </div>
        </div>
        <ScoreRing
          score={area.score}
          size={180}
          label={`${area.completed}/${area.due} today`}
          sub={area.score == null ? "no score yet" : "area score"}
        />
      </div>

      <section className="card checklist-card" style={{ marginTop: 24 }}>
        <div className="checklist-toolbar">
          <div>
            <h2>Your list</h2>
            <p className="muted small">Walk. Gym. A game. Whatever you actually do.</p>
          </div>
          {weekDays.length ? (
            <div className="checklist-weekdays" aria-hidden="true">
              {weekDays.map((day) => (
                <span key={day.date} className={day.is_today ? "today-col" : ""}>
                  {day.weekday.slice(0, 2)}
                </span>
              ))}
            </div>
          ) : null}
        </div>
        <AreaChecklist area={area} weekDays={weekDays} onChanged={load} showHeader={false} />
      </section>

      <section className="card" style={{ marginTop: 20 }}>
        <h2>Need a counted goal?</h2>
        <p className="muted small">Minutes, glasses, pages — the name is yours.</p>
        <form className="stack" style={{ marginTop: 16 }} onSubmit={addPractice}>
          <input placeholder="Name it" value={name} onChange={(e) => setName(e.target.value)} required />
          <div className="row">
            <button type="button" className={kind === "check" ? "" : "secondary"} onClick={() => setKind("check")}>
              Check
            </button>
            <button type="button" className={kind === "count" ? "" : "secondary"} onClick={() => setKind("count")}>
              Count
            </button>
          </div>
          {kind === "count" ? (
            <div className="row">
              <input
                type="number"
                min={1}
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                style={{ maxWidth: 120 }}
              />
              <input value={unit} onChange={(e) => setUnit(e.target.value)} style={{ maxWidth: 160 }} />
            </div>
          ) : null}
          {error ? <p className="error">{error}</p> : null}
          <button type="submit" disabled={busy}>
            {busy ? "Adding…" : "Add"}
          </button>
        </form>
      </section>
    </main>
  );
}
