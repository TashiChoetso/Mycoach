"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { AreaChecklist } from "@/components/ChecklistRow";
import { GreetingClock } from "@/components/GreetingClock";
import { PriorityCard } from "@/components/PriorityCard";
import { ScoreRing } from "@/components/ScoreRing";
import { WeekGlance } from "@/components/WeekGlance";
import { CalendarDay, TodayPayload, today } from "@/lib/api";

function weekday(iso: string) {
  return new Date(`${iso}T12:00:00`).toLocaleDateString(undefined, { weekday: "short" });
}

function fallbackWeekDays(date?: string): CalendarDay[] {
  const anchor = date ? new Date(`${date}T12:00:00`) : new Date();
  const day = anchor.getDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;
  const monday = new Date(anchor);
  monday.setDate(anchor.getDate() + mondayOffset);
  return Array.from({ length: 7 }, (_, index) => {
    const item = new Date(monday);
    item.setDate(monday.getDate() + index);
    const iso = item.toISOString().slice(0, 10);
    return {
      date: iso,
      weekday: item.toLocaleDateString(undefined, { weekday: "short" }),
      is_today: iso === date,
      is_future: item > anchor,
    };
  });
}

export default function TodayPage() {
  const router = useRouter();
  const [data, setData] = useState<TodayPayload | null>(null);
  const [error, setError] = useState("");

  async function load() {
    const payload = await today();
    setData(payload);
  }

  useEffect(() => {
    load().catch(() => {
      setError("Please sign in again.");
      router.push("/login");
    });
  }, [router]);

  if (!data) {
    return (
      <main className="shell wide">
        <p className="muted" suppressHydrationWarning>
          {error || "Laying out the day…"}
        </p>
      </main>
    );
  }

  const due = data.momentum.due ?? 0;
  const completed = data.momentum.completed ?? 0;
  const weekDays = data.week_days?.length ? data.week_days : fallbackWeekDays(data.date);
  const priorities = data.priorities ?? { day: "", month: "" };

  return (
    <main className="shell wide">
      <AppNav active="today" />

      <div className="widget-board">
        <GreetingClock hello={data.greeting.hello} quote={data.greeting.quote} date={data.date} />
        <WeekGlance days={weekDays} />

        <div className="span-2">
          <PriorityCard
            day={priorities.day}
            month={priorities.month}
            onChanged={(next) => setData((current) => (current ? { ...current, priorities: next } : current))}
          />
        </div>

        <section className="widget checklist-card span-2">
          <div className="checklist-toolbar">
            <div>
              <h2>This week</h2>
              <p className="muted small">Write your own names. A check is enough.</p>
            </div>
            <div className="checklist-weekdays" aria-hidden="true">
              {weekDays.map((day) => (
                <span key={day.date} className={day.is_today ? "today-col" : ""}>
                  {day.weekday.slice(0, 2)}
                </span>
              ))}
            </div>
          </div>
          {data.areas.length === 0 ? (
            <p className="muted">
              <Link href="/onboarding/areas">Choose a part of life first.</Link>
            </p>
          ) : (
            data.areas.map((area) => (
              <AreaChecklist key={area.id} area={area} weekDays={weekDays} onChanged={load} />
            ))
          )}
        </section>

        <section className="widget momentum-card">
          <p className="eyebrow">Momentum</p>
          <ScoreRing
            score={data.momentum.score}
            rest={data.momentum.rest_day}
            label={data.momentum.rest_day ? "rest" : "of 100"}
            sub={data.momentum.label}
          />
          <p className="muted small" style={{ marginTop: 8 }}>
            {data.momentum.rest_day
              ? "No score until you add a practice and check it."
              : `${completed}/${due} followed through.`}
          </p>
          {data.week?.length ? (
            <div className="week">
              {data.week.map((day) => (
                <div key={day.date} className={`week-cell ${day.date === data.date ? "today" : ""}`}>
                  <span>{weekday(day.date)}</span>
                  <strong>{day.score == null ? "—" : day.score}</strong>
                </div>
              ))}
            </div>
          ) : null}
        </section>

        {data.coach ? (
          <section className="widget coach-widget">
            <p className="eyebrow">A note</p>
            <p className="coach-copy">{data.coach.message}</p>
          </section>
        ) : null}
      </div>
    </main>
  );
}
