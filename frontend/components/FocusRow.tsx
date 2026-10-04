"use client";

import { useState } from "react";
import { FocusItem, completeFocus, skipFocus, undoFocus } from "@/lib/api";

type FocusRowProps = {
  focus: FocusItem;
  onChanged: () => Promise<void> | void;
  date?: string;
};

export function FocusRow({ focus, onChanged, date }: FocusRowProps) {
  const [busy, setBusy] = useState(false);
  const [count, setCount] = useState(
    focus.value ?? (focus.kind === "count" ? 0 : 0)
  );
  const done = focus.status === "completed";
  const skipped = focus.status === "skipped";

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

  const target = focus.target_value ?? 0;

  return (
    <div className={`focus-row ${done ? "done" : ""} ${skipped ? "skipped" : ""}`}>
      <button
        type="button"
        className={`check ${done ? "on" : ""}`}
        aria-label={done ? `Undo ${focus.name}` : `Complete ${focus.name}`}
        disabled={busy}
        onClick={() =>
          run(() =>
            done
              ? undoFocus(focus.id, date)
              : completeFocus(focus.id, focus.kind === "count" ? count || target || 1 : undefined, date)
          )
        }
      />
      <div className="focus-copy">
        <div className="focus-title">
          <strong>{focus.name}</strong>
          {typeof focus.score === "number" && (done || skipped) ? (
            <span className="muted small">{skipped ? "Skipped" : `${focus.score}`}</span>
          ) : null}
        </div>
        {focus.prompt ? <p className="muted small">{focus.prompt}</p> : null}
        {focus.kind === "count" ? (
          <div className="stepper">
            <button
              type="button"
              className="ghost"
              disabled={busy}
              onClick={() => setCount((n) => Math.max(0, n - 1))}
            >
              −
            </button>
            <span>
              {done ? focus.value ?? count : count}
              {focus.unit ? ` ${focus.unit}` : ""}
              {target ? ` / ${target}` : ""}
            </span>
            <button
              type="button"
              className="ghost"
              disabled={busy}
              onClick={() => setCount((n) => n + 1)}
            >
              +
            </button>
            {!done ? (
              <button
                type="button"
                className="secondary"
                disabled={busy}
                onClick={() => run(() => completeFocus(focus.id, count || target || 1, date))}
              >
                Log
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
      <button
        type="button"
        className="ghost small skip"
        disabled={busy}
        onClick={() => run(() => (skipped ? undoFocus(focus.id, date) : skipFocus(focus.id, date)))}
      >
        {skipped ? "Unskip" : "Skip"}
      </button>
    </div>
  );
}
