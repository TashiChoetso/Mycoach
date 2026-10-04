"use client";

import { ReactNode, useEffect, useMemo, useState } from "react";

type CalmHorizonProps = {
  children?: ReactNode;
  compact?: boolean;
};

const MOTES = [
  { left: "6%", top: "16%", size: 7, duration: 22, delay: 0 },
  { left: "12%", top: "42%", size: 4, duration: 18, delay: 3 },
  { left: "18%", top: "8%", size: 5, duration: 26, delay: 7 },
  { left: "28%", top: "28%", size: 3, duration: 16, delay: 1 },
  { left: "36%", top: "12%", size: 6, duration: 24, delay: 5 },
  { left: "48%", top: "22%", size: 4, duration: 20, delay: 2 },
  { left: "58%", top: "6%", size: 5, duration: 28, delay: 8 },
  { left: "67%", top: "18%", size: 8, duration: 21, delay: 4 },
  { left: "74%", top: "38%", size: 4, duration: 19, delay: 6 },
  { left: "82%", top: "12%", size: 6, duration: 23, delay: 1.5 },
  { left: "88%", top: "32%", size: 3, duration: 17, delay: 9 },
  { left: "91%", top: "48%", size: 5, duration: 25, delay: 3.5 },
  { left: "41%", top: "48%", size: 3, duration: 15, delay: 11 },
  { left: "22%", top: "58%", size: 4, duration: 21, delay: 6.5 },
  { left: "63%", top: "54%", size: 7, duration: 27, delay: 2.2 },
  { left: "78%", top: "62%", size: 3, duration: 18, delay: 10 },
];

export function CalmHorizon({ children, compact = false }: CalmHorizonProps) {
  const [paused, setPaused] = useState(false);
  const [parallax, setParallax] = useState({ x: 0, y: 0 });
  const [sunGlow, setSunGlow] = useState(false);
  const reduceMotion = useMemo(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  useEffect(() => {
    if (!reduceMotion) return;
    setPaused(true);
  }, [reduceMotion]);

  return (
    <section
      className={`calm-horizon ${compact ? "is-compact" : ""} ${paused ? "is-paused" : ""}`}
      onPointerMove={(event) => {
        if (paused || reduceMotion) return;
        const box = event.currentTarget.getBoundingClientRect();
        setParallax({
          x: (event.clientX - box.left) / box.width - 0.5,
          y: (event.clientY - box.top) / box.height - 0.5,
        });
      }}
      onPointerLeave={() => setParallax({ x: 0, y: 0 })}
    >
      <div
        className="calm-sun-wrap"
        style={{ transform: `translate(${parallax.x * 22}px, ${parallax.y * 14}px)` }}
      >
        <button
          type="button"
          className={`calm-sun ${sunGlow ? "is-glowing" : ""}`}
          aria-label="Warm the sun"
          onClick={() => {
            setSunGlow(true);
            window.setTimeout(() => setSunGlow(false), 1400);
          }}
        />
      </div>

      <svg
        className="calm-fuji"
        viewBox="0 0 1440 900"
        preserveAspectRatio="xMidYMax slice"
        aria-hidden="true"
        style={{ transform: `translate(${parallax.x * 10}px, ${parallax.y * 6}px)` }}
      >
        <path d="M40 900 L360 720 L700 900 Z" fill="#c5c8e8" />
        <path d="M120 900 L700 560 Q800 430 900 560 L1480 900 Z" fill="#7a81c6" />
        <path d="M800 495 L1480 900 L900 560 Q800 430 700 560 Z" fill="#6c73bc" opacity="0.28" />
        <g fill="#fbf8f3">
          <ellipse cx="800" cy="500" rx="110" ry="70" />
          <ellipse cx="722" cy="528" rx="70" ry="48" />
          <ellipse cx="878" cy="526" rx="66" ry="46" />
        </g>
      </svg>

      <div className="calm-mist" />

      <div className="calm-motes" style={{ transform: `translate(${parallax.x * 28}px, ${parallax.y * 18}px)` }}>
        {MOTES.map((mote, index) => (
          <span
            key={index}
            className="calm-mote"
            style={{
              left: mote.left,
              top: mote.top,
              width: mote.size,
              height: mote.size,
              animationDuration: `${mote.duration}s`,
              animationDelay: `${mote.delay}s`,
            }}
          />
        ))}
      </div>

      <div className="calm-overlay">{children}</div>
    </section>
  );
}
