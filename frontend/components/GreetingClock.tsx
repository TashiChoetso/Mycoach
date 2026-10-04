"use client";

import { useEffect, useState } from "react";

type GreetingClockProps = {
  hello: string;
  quote: string;
  date?: string;
};

export function GreetingClock({ hello, quote, date }: GreetingClockProps) {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const id = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const hours = now ? String(now.getHours()).padStart(2, "0") : "··";
  const minutes = now ? String(now.getMinutes()).padStart(2, "0") : "··";
  const meridian = now ? (now.getHours() >= 12 ? "PM" : "AM") : "";
  const dayLabel = (date ? new Date(`${date}T12:00:00`) : now)?.toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  return (
    <section className="widget greeting-clock">
      <p className="greeting-hello">{hello}</p>
      <div className="flip-clock" aria-label={now ? now.toLocaleTimeString() : "Time"}>
        <span className="flip-tile">{hours}</span>
        <span className="flip-colon" aria-hidden="true">
          :
        </span>
        <span className="flip-tile">{minutes}</span>
        <span className="flip-meridian">{meridian}</span>
      </div>
      <p className="greeting-date">{dayLabel}</p>
      <p className="greeting-quote">{quote}</p>
    </section>
  );
}
