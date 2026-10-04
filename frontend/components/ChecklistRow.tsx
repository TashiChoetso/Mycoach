"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import {
  AreaBoard,
  CalendarDay,
  FocusItem,
  completeFocus,
  createFocus,
  deleteFocus,
  undoFocus,
} from "@/lib/api";

function markFor(focus: FocusItem, day: CalendarDay) {
  return focus.marks?.find((item) => item.date === day.date)?.status ?? "open";
}

type ChecklistRowProps = {
  focus: FocusItem;
  weekDays: CalendarDay[];
  onChanged: () => Promise<void> | void;
};

export function ChecklistRow({ focus, weekDays, onChanged }: ChecklistRowProps) {
  const [busy, setBusy] = useState(false);

  async function run(action: () => Promise<unknown>) {
    if (busy) return;
    setBusy(true);
    try {
      await action();
      await onChanged();
    } finally {
      setBusy(false);
    }
  }

  function toggle(day: CalendarDay) {
    if (day.is_future || busy) return;
    const status = markFor(focus, day);
    const value = focus.kind === "count" ? focus.target_value ?? focus.value ?? 1 : undefined;
    run(() =>
      status === "completed" ? undoFocus(focus.id, day.date) : completeFocus(focus.id, value, day.date)
    );
  }

  return (
    <div className={`checklist-row ${busy ? "busy" : ""}`}>
      <div className="checklist-name">
        <strong>{focus.name}</strong>
        {focus.kind === "count" && focus.target_value ? (
          <span className="muted small">
            {focus.target_value}
            {focus.unit ? ` ${focus.unit}` : ""}
          </span>
        ) : null}
      </div>
      <div className="checklist-marks">
        {weekDays.map((day) => {
          const status = markFor(focus, day);
          const done = status === "completed";
          return (
            <button
              key={day.date}
              type="button"
              className={`week-mark ${done ? "done" : ""} ${day.is_today ? "today-col" : ""} ${
                day.is_future ? "future" : ""
              }`}
              aria-label={`${focus.name} ${day.weekday}`}
              disabled={busy || day.is_future}
              onClick={() => toggle(day)}
            >
              {done ? "✓" : ""}
            </button>
          );
        })}
      </div>
      <button
        type="button"
        className="ghost small checklist-remove"
        aria-label={`Remove ${focus.name}`}
        disabled={busy}
        onClick={() => run(() => deleteFocus(focus.id))}
      >
        ×
      </button>
    </div>
  );
}

type AreaChecklistProps = {
  area: AreaBoard;
  weekDays: CalendarDay[];
  onChanged: () => Promise<void> | void;
  showHeader?: boolean;
};

export function AreaChecklist({ area, weekDays, onChanged, showHeader = true }: AreaChecklistProps) {
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);

  async function addItem(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim() || busy) return;
    setBusy(true);
    try {
      await createFocus({ user_area_id: area.id, name: draft.trim(), kind: "check" });
      setDraft("");
      await onChanged();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="practice-group">
      {showHeader ? (
        <div className="checklist-row is-header">
          <div className="checklist-name">
            <Link href={`/areas/${area.id}`}>{area.name}</Link>
            <span className="muted small">
              {area.due === 0
                ? "Add something to do"
                : area.score == null
                  ? `${area.completed}/${area.due}`
                  : `${area.score} · ${area.completed}/${area.due}`}
            </span>
          </div>
        </div>
      ) : null}
      {area.focuses.map((focus) => (
        <ChecklistRow key={focus.id} focus={focus} weekDays={weekDays} onChanged={onChanged} />
      ))}
      <form className="checklist-add" onSubmit={addItem}>
        <button type="submit" className="ghost" aria-label={`Add to ${area.name}`} disabled={busy}>
          +
        </button>
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={`Add to ${area.name}`}
          maxLength={120}
          disabled={busy}
        />
      </form>
    </div>
  );
}
