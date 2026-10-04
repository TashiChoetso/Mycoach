"use client";

import { useEffect, useState } from "react";
import { setPriority } from "@/lib/api";

type PriorityCardProps = {
  day: string;
  month: string;
  onChanged?: (next: { day: string; month: string }) => void;
};

export function PriorityCard({ day, month, onChanged }: PriorityCardProps) {
  const [dayText, setDayText] = useState(day);
  const [monthText, setMonthText] = useState(month);

  useEffect(() => setDayText(day), [day]);
  useEffect(() => setMonthText(month), [month]);

  async function save(period: "day" | "month", text: string) {
    const next = await setPriority(period, text);
    onChanged?.(next);
  }

  return (
    <div className="priority-grid">
      <label className="widget priority-field">
        <span className="eyebrow">This month</span>
        <textarea
          rows={2}
          value={monthText}
          placeholder="What this month is for."
          maxLength={400}
          onChange={(event) => setMonthText(event.target.value)}
          onBlur={() => {
            if (monthText.trim() !== month.trim()) save("month", monthText);
          }}
        />
      </label>
      <label className="widget priority-field">
        <span className="eyebrow">Today</span>
        <textarea
          rows={2}
          value={dayText}
          placeholder="The one thing that would make today enough."
          maxLength={400}
          onChange={(event) => setDayText(event.target.value)}
          onBlur={() => {
            if (dayText.trim() !== day.trim()) save("day", dayText);
          }}
        />
      </label>
    </div>
  );
}
