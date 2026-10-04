"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { PracticeChip } from "@/components/PracticeChip";
import { ScoreRing } from "@/components/ScoreRing";
import { TrendChart } from "@/components/TrendChart";
import { ProgressPayload, progress } from "@/lib/api";

type Range = "day" | "week" | "month";

function pretty(iso: string) {
  return new Date(`${iso}T12:00:00`).toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

export default function ProgressPage() {
  const router = useRouter();
  const [range, setRange] = useState<Range>("week");
  const [offset, setOffset] = useState(0);
  const [view, setView] = useState<"board" | "chart">("board");
  const [data, setData] = useState<ProgressPayload | null>(null);
  const [error, setError] = useState("");

  async function load(nextRange = range, nextOffset = offset) {
    const payload = await progress(nextRange, nextOffset);
    setData(payload);
  }

  useEffect(() => {
    load().catch(() => {
      setError("Please sign in again.");
      router.push("/login");
    });
  }, [router]);

  async function changeRange(next: Range) {
    setRange(next);
    setOffset(0);
    setView(next === "month" ? "chart" : "board");
    await load(next, 0);
  }

  async function changeOffset(next: number) {
    setOffset(next);
    await load(range, next);
  }

  if (!data) {
    return (
      <main className="shell wide">
        <p className="muted">{error || "Loading your progress…"}</p>
      </main>
    );
  }

  const summaryScore = data.summary.score;
  const rest = summaryScore == null;

  return (
    <main className="shell wide progress-shell">
      <AppNav active="progress" />
      <p className="eyebrow">Follow-through</p>
      <h1>See the week. Keep the score honest.</h1>
      <p className="lede">
        Same practices as Today — now laid out day by day, week by week, and month by month. The
        graph never invents a number.
      </p>

      <div className="range-bar">
        <div className="segment">
          {(["day", "week", "month"] as Range[]).map((item) => (
            <button key={item} type="button" className={range === item ? "" : "secondary"} onClick={() => changeRange(item)}>
              {item[0].toUpperCase() + item.slice(1)}
            </button>
          ))}
        </div>
        <div className="segment">
          <button type="button" className={view === "board" ? "" : "secondary"} onClick={() => setView("board")}>
            Board
          </button>
          <button type="button" className={view === "chart" ? "" : "secondary"} onClick={() => setView("chart")}>
            Chart
          </button>
        </div>
      </div>

      <div className="track-layout">
        <section className="card momentum-card">
          <p className="eyebrow">{data.label}</p>
          <ScoreRing
            score={summaryScore}
            rest={rest}
            label={rest ? "No score yet" : "average"}
            sub={`${data.summary.completed} logged`}
          />
          <dl className="stat-grid">
            <div>
              <dt>Active days</dt>
              <dd>{data.summary.days_active}</dd>
            </div>
            <div>
              <dt>Streak</dt>
              <dd>{data.summary.streak}</dd>
            </div>
            <div>
              <dt>Best</dt>
              <dd>{data.summary.best?.score ?? "—"}</dd>
            </div>
          </dl>
        </section>

        <section className="card track-main">
          {range === "week" ? (
            <div className="week-tabs">
              {data.weeks.map((week) => (
                <button
                  key={week.offset}
                  type="button"
                  className={`week-tab ${offset === week.offset ? "on" : ""}`}
                  onClick={() => changeOffset(week.offset)}
                >
                  {week.label}
                </button>
              ))}
            </div>
          ) : null}
          {range === "month" ? (
            <div className="week-tabs">
              <button type="button" className={`week-tab ${offset === 0 ? "on" : ""}`} onClick={() => changeOffset(0)}>
                This month
              </button>
              <button type="button" className={`week-tab ${offset === 1 ? "on" : ""}`} onClick={() => changeOffset(1)}>
                Last month
              </button>
            </div>
          ) : null}

          {view === "chart" ? (
            <>
              <div className="section-head">
                <h2>Momentum</h2>
                <p className="muted small">
                  {pretty(data.start)} – {pretty(data.end)}
                </p>
              </div>
              <TrendChart series={data.series} />
            </>
          ) : range === "month" ? (
            <MonthBoard data={data} />
          ) : range === "day" ? (
            <DayBoard data={data} onChanged={() => load()} />
          ) : (
            <WeekBoard data={data} onChanged={() => load()} />
          )}
        </section>
      </div>

      {data.areas.length ? (
        <section style={{ marginTop: 28 }}>
          <div className="section-head">
            <h2>By life area</h2>
            <p className="muted small">Averages for this {range} — still from the same practices.</p>
          </div>
          <div className="area-bars">
            {data.areas.map((area) => (
              <a key={area.id} href={`/areas/${area.id}`} className={`area-bar tone-${area.tone}`}>
                <div className="area-bar-copy">
                  <strong>{area.name}</strong>
                  <span>
                    {area.completed}/{area.due} practices
                  </span>
                </div>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: area.score == null ? "0%" : `${area.score}%` }} />
                </div>
                <em>{area.score == null ? "—" : area.score}</em>
              </a>
            ))}
          </div>
        </section>
      ) : null}
    </main>
  );
}

function WeekBoard({ data, onChanged }: { data: ProgressPayload; onChanged: () => Promise<void> | void }) {
  return (
    <div className="week-split">
      {data.days.map((day, index) => (
        <article key={day.date} className={`day-col d${index % 7} ${day.is_today ? "is-today" : ""}`}>
          <header>
            <span>{day.weekday}</span>
            <strong>{pretty(day.date)}</strong>
            <em>{day.is_future ? "Coming" : day.score == null ? "—" : day.score}</em>
          </header>
          {day.areas?.map((area) => (
            <div key={area.id} className="day-area">
              <p>{area.name}</p>
              {(area.focuses || []).slice(0, 6).map((focus) => (
                <PracticeChip
                  key={focus.id}
                  focus={focus}
                  date={day.date}
                  future={day.is_future}
                  onChanged={onChanged}
                />
              ))}
            </div>
          ))}
        </article>
      ))}
    </div>
  );
}

function DayBoard({ data, onChanged }: { data: ProgressPayload; onChanged: () => Promise<void> | void }) {
  const day = data.days[0];
  if (!day) return <p className="muted">Nothing on this day.</p>;
  return (
    <div>
      <div className="section-head">
        <h2>{day.is_today ? "Today" : pretty(day.date)}</h2>
        <p className="muted small">{day.completed} of {day.due} done</p>
      </div>
      <TrendChart series={data.series} height={160} />
      {day.areas?.map((area) => (
        <div key={area.id} className="practice-group">
          <div className="practice-group-head">
            <span>{area.name}</span>
            <span className="muted small">{area.score == null ? "—" : area.score}</span>
          </div>
          {(area.focuses || []).map((focus) => (
            <PracticeChip key={focus.id} focus={focus} date={day.date} onChanged={onChanged} />
          ))}
        </div>
      ))}
    </div>
  );
}

function MonthBoard({ data }: { data: ProgressPayload }) {
  return (
    <div>
      <div className="section-head">
        <h2>{data.label}</h2>
        <p className="muted small">Darker cells mean a stronger day.</p>
      </div>
      <div className="month-heat">
        {data.calendar.slice(0, 7).map((day) => (
          <span key={day.date} className="heat-label">
            {day.weekday[0]}
          </span>
        ))}
        {data.calendar.map((day) => {
          const scored = day.in_month && day.score != null;
          return (
          <div
            key={day.date}
            className={`heat-cell ${day.in_month ? "" : "out"} ${day.is_today ? "is-today" : ""} ${
              day.in_month && day.score == null ? "rest" : ""
            }`}
            style={{
              background: scored
                ? `rgba(36, 92, 74, ${0.1 + (day.score! / 100) * 0.75})`
                : day.in_month
                  ? "transparent"
                  : "transparent",
              color: scored && day.score! > 55 ? "#f7f3ec" : "inherit",
            }}
            title={`${day.date}: ${day.score ?? "—"}`}
          >
            {Number(day.date.slice(8))}
          </div>
          );
        })}      </div>
      <TrendChart series={data.series} />
    </div>
  );
}
