"use client";

import { useMemo, useState } from "react";

const PETALS = [
  { left: "8%", delay: 0, duration: 14, size: 8, drift: 18 },
  { left: "22%", delay: 3, duration: 16, size: 7, drift: -12 },
  { left: "38%", delay: 1, duration: 13, size: 9, drift: 22 },
  { left: "54%", delay: 6, duration: 18, size: 6, drift: -16 },
  { left: "68%", delay: 2, duration: 15, size: 8, drift: 10 },
  { left: "82%", delay: 5, duration: 17, size: 7, drift: -20 },
  { left: "14%", delay: 8, duration: 12, size: 6, drift: 14 },
  { left: "46%", delay: 4, duration: 19, size: 8, drift: -8 },
  { left: "74%", delay: 7, duration: 14, size: 7, drift: 16 },
];

type Ripple = { id: number; x: number; y: number };

type SakuraSanctuaryProps = {
  variant?: "widget" | "edge";
  bloom?: number | null;
};

export function SakuraSanctuary({ variant = "widget", bloom = 40 }: SakuraSanctuaryProps) {
  const [lanternOn, setLanternOn] = useState(false);
  const [ripples, setRipples] = useState<Ripple[]>([]);
  const reduceMotion = useMemo(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  const level = bloom == null ? 0 : Math.max(0, Math.min(100, bloom));
  const blossom = 0.28 + (level / 100) * 0.72;
  const petalCount = variant === "edge" ? 4 : level === 0 ? 0 : Math.max(3, Math.round((level / 100) * PETALS.length));
  const lit = lanternOn || level >= 60;

  return (
    <div
      className={`sakura-scene is-${variant} ${reduceMotion ? "is-still" : ""}`}
      onPointerDown={(event) => {
        if (reduceMotion || variant === "edge") return;
        const box = event.currentTarget.getBoundingClientRect();
        const next = {
          id: Date.now(),
          x: event.clientX - box.left,
          y: event.clientY - box.top,
        };
        setRipples((current) => [...current.slice(-4), next]);
      }}
    >
      <div className="sakura-ground" />
      {variant === "widget" ? (
        <svg className="sakura-ripples-svg" viewBox="0 0 900 280" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
          <ellipse cx="280" cy="240" rx="240" ry="28" fill="none" stroke="rgba(79, 93, 69, 0.18)" strokeWidth="2" />
          <ellipse cx="300" cy="255" rx="300" ry="22" fill="none" stroke="rgba(79, 93, 69, 0.12)" strokeWidth="2" />
          <ellipse cx="160" cy="248" rx="28" ry="9" fill="rgba(79, 93, 69, 0.22)" />
          <ellipse cx="230" cy="254" rx="24" ry="8" fill="rgba(79, 93, 69, 0.18)" />
          <ellipse cx="300" cy="250" rx="30" ry="9" fill="rgba(79, 93, 69, 0.22)" />
          <ellipse cx="380" cy="256" rx="22" ry="8" fill="rgba(79, 93, 69, 0.16)" />
        </svg>
      ) : null}

      {ripples.map((ripple) => (
        <span
          key={ripple.id}
          className="sakura-ripple"
          style={{ left: ripple.x, top: ripple.y }}
          onAnimationEnd={() => setRipples((current) => current.filter((item) => item.id !== ripple.id))}
        />
      ))}

      {variant === "widget" ? (
        <button
          type="button"
          className={`sakura-lantern ${lit ? "is-lit" : ""}`}
          aria-label="Light the lantern"
          onClick={(event) => {
            event.stopPropagation();
            setLanternOn((value) => !value);
          }}
          onPointerDown={(event) => event.stopPropagation()}
        >
          <span className="sakura-lantern-glow" />
          <span className="sakura-lantern-light" />
          <span className="sakura-lantern-post" />
        </button>
      ) : null}

      <svg className="sakura-tree" viewBox="0 0 640 720" aria-hidden="true">
        <path
          d="M430 720 C428 560 410 470 360 390 C430 430 520 360 560 250"
          fill="none"
          stroke="#7a5340"
          strokeWidth="22"
          strokeLinecap="round"
        />
        <path
          d="M390 430 C300 360 240 280 210 180"
          fill="none"
          stroke="#7a5340"
          strokeWidth="14"
          strokeLinecap="round"
        />
        <path
          d="M500 330 C560 280 610 220 640 140"
          fill="none"
          stroke="#6b4636"
          strokeWidth="12"
          strokeLinecap="round"
        />
        <g opacity={blossom}>
          <circle cx="548" cy="228" r="42" fill="#f3c1c8" />
          <circle cx="500" cy="198" r="36" fill="#e8a8b4" opacity="0.92" />
          <circle cx="590" cy="186" r="34" fill="#f7d3d8" opacity="0.9" />
          <circle cx="528" cy="158" r="28" fill="#f0b7c0" />
          {level > 35 ? (
            <>
              <circle cx="220" cy="168" r="32" fill="#f3c1c8" />
              <circle cx="188" cy="138" r="24" fill="#e8a8b4" />
              <circle cx="252" cy="132" r="22" fill="#f7d3d8" />
            </>
          ) : null}
        </g>
      </svg>

      {PETALS.slice(0, petalCount).map((petal, index) => (
        <span
          key={index}
          className="sakura-petal"
          style={{
            left: petal.left,
            width: petal.size,
            height: petal.size * 0.62,
            animationDuration: `${petal.duration}s`,
            animationDelay: `${petal.delay}s`,
            ["--drift" as string]: `${petal.drift}px`,
          }}
        />
      ))}
    </div>
  );
}
