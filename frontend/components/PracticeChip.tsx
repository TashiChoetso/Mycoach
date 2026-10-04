"use client";

import { FocusItem, completeFocus, undoFocus } from "@/lib/api";

type PracticeChipProps = {
  focus: FocusItem;
  date: string;
  future?: boolean;
  onChanged: () => Promise<void> | void;
};

export function PracticeChip({ focus, date, future, onChanged }: PracticeChipProps) {
  const done = focus.status === "completed";
  const upcoming = future || focus.status === "upcoming";

  async function toggle() {
    if (upcoming) return;
    if (done) await undoFocus(focus.id, date);
    else await completeFocus(focus.id, focus.kind === "count" ? focus.target_value || 1 : undefined, date);
    await onChanged();
  }

  return (
    <button
      type="button"
      className={`practice-chip ${done ? "done" : ""} ${upcoming ? "soon" : ""}`}
      onClick={toggle}
      disabled={upcoming}
    >
      <span className="chip-mark">{upcoming ? "•" : done ? "✓" : ""}</span>
      <span>{focus.name}</span>
    </button>
  );
}
