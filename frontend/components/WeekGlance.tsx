import { CalendarDay } from "@/lib/api";

type WeekGlanceProps = {
  days: CalendarDay[];
};

export function WeekGlance({ days }: WeekGlanceProps) {
  return (
    <section className="widget week-glance">
      <p className="eyebrow">This week</p>
      <div className="glance-grid">
        {days.map((day) => (
          <div key={day.date} className={`glance-cell ${day.is_today ? "today" : ""} ${day.is_future ? "future" : ""}`}>
            <span>{day.weekday.slice(0, 2)}</span>
            <strong>{Number(day.date.slice(-2))}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
