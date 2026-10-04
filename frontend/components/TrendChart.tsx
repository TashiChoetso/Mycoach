import { ProgressDay } from "@/lib/api";

type TrendChartProps = {
  series: ProgressDay[];
  height?: number;
};

type Point = { x: number; y: number; row: ProgressDay; scored: boolean };

export function TrendChart({ series, height = 220 }: TrendChartProps) {
  const width = 640;
  const pad = { top: 18, right: 16, bottom: 28, left: 28 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const rows = series.filter((row) => !row.is_future);
  const plot = rows.length ? rows : series;
  const points: Point[] = plot.map((row, index) => {
    const x = plot.length <= 1 ? innerW / 2 : (index / Math.max(plot.length - 1, 1)) * innerW;
    const scored = row.score != null;
    const value = scored ? row.score! : 0;
    const y = scored ? innerH - (value / 100) * innerH : pad.top + innerH;
    return { x: x + pad.left, y: y + pad.top, row, scored };
  });

  // Draw line segments only through real scores — rest / empty days are gaps, not zeros.
  const segments: string[] = [];
  let path = "";
  for (const point of points) {
    if (!point.scored) {
      if (path) segments.push(path);
      path = "";
      continue;
    }
    path += path ? ` L ${point.x} ${point.y}` : `M ${point.x} ${point.y}`;
  }
  if (path) segments.push(path);

  const areaPaths = segments.map((line) => {
    const coords = [...line.matchAll(/([ML])\s+([\d.]+)\s+([\d.]+)/g)].map((m) => ({
      x: Number(m[2]),
      y: Number(m[3]),
    }));
    if (coords.length < 2) return "";
    const first = coords[0];
    const last = coords[coords.length - 1];
    return `${line} L ${last.x} ${pad.top + innerH} L ${first.x} ${pad.top + innerH} Z`;
  });

  const ticks = [0, 50, 100];
  const labelEvery = Math.max(1, Math.ceil(points.length / 7));

  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} className="trend-chart" role="img" aria-label="Momentum over time">
        {ticks.map((tick) => {
          const y = pad.top + innerH - (tick / 100) * innerH;
          return (
            <g key={tick}>
              <line x1={pad.left} x2={width - pad.right} y1={y} y2={y} className="chart-grid" />
              <text x={4} y={y + 4} className="chart-tick">
                {tick}
              </text>
            </g>
          );
        })}
        {areaPaths.map((area, index) => (area ? <path key={`a${index}`} d={area} className="chart-area" /> : null))}
        {segments.map((line, index) => (
          <path key={`l${index}`} d={line} className="chart-line" />
        ))}
        {points.map((point) =>
          point.scored ? (
            <circle
              key={point.row.date}
              cx={point.x}
              cy={point.y}
              r={point.row.is_today ? 6 : 4}
              className="chart-dot"
            />
          ) : (
            <circle
              key={point.row.date}
              cx={point.x}
              cy={pad.top + innerH}
              r={3}
              className="chart-dot empty"
            />
          )
        )}
        {points.map((point, index) =>
          index % labelEvery === 0 || index === points.length - 1 ? (
            <text key={`${point.row.date}-l`} x={point.x} y={height - 8} textAnchor="middle" className="chart-tick">
              {point.row.weekday || point.row.date.slice(8)}
            </text>
          ) : null
        )}
      </svg>
    </div>
  );
}
