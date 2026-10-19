/**
 * Shared categorical palette for multi-series charts, from the reference app.
 * Keep the order stable — pages cycle through it with
 * `CHART_COLORS[index % CHART_COLORS.length]`, so a category keeps its color
 * across reloads while the response's category order is stable. The one place
 * raw hex is allowed; everything else uses theme tokens.
 */
export const CHART_COLORS: readonly string[] = [
  '#2563eb', // blue
  '#dc2626', // red
  '#16a34a', // green
  '#9333ea', // purple
  '#ea580c', // orange
  '#0891b2', // cyan
  '#be185d', // pink
  '#65a30d', // lime
] as const

/** Two-series current-vs-previous charts use the theme's first two chart tokens. */
export const SERIES = {
  current: 'var(--chart-1)',
  previous: 'var(--chart-2)',
} as const
