type ScoreRingProps = {
  score: number | null;
  size?: number;
  label?: string;
  sub?: string;
  rest?: boolean;
};

export function ScoreRing({ score, size = 168, label, sub, rest }: ScoreRingProps) {
  const stroke = 8;
  const radius = (size - stroke) / 2 - 2;
  const circ = 2 * Math.PI * radius;
  const shown = rest || score == null ? 0 : Math.max(0, Math.min(100, score)) / 100;
  const dash = `${circ * shown} ${circ}`;
  const text = rest || score == null ? "—" : String(score);

  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(28,24,20,0.08)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={dash}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="ring-label">
        <strong>{text}</strong>
        {label ? <span>{label}</span> : null}
        {sub ? <em>{sub}</em> : null}
      </div>
    </div>
  );
}
