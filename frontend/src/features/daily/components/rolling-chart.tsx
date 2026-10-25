import { CartesianGrid, Line, LineChart, XAxis, YAxis } from 'recharts'
import { ChartContainer, ChartTooltip } from '@/components/ui/chart'
import type { ChartConfig } from '@/components/ui/chart'
import { formatShortDate } from '@/lib/format'
import type { RollingAverage } from '../api'

type RollingPoint = NonNullable<RollingAverage['points']>[number]

type RollingChartProps = {
  points: RollingPoint[]
  dataKey: 'rolling_average' | 'projected_monthly'
  label: string
  format: (value: number) => string
}

/** One rolling series over time; a point without a full window is a gap. */
export function RollingChart({
  points,
  dataKey,
  label,
  format,
}: RollingChartProps) {
  const config = {
    [dataKey]: { label, color: 'var(--chart-1)' },
  } satisfies ChartConfig
  const byDate = new Map(points.map((p) => [p.record_date, p]))
  return (
    <ChartContainer config={config} className='aspect-auto h-72 w-full'>
      <LineChart
        data={points}
        margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
      >
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey='record_date'
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          minTickGap={32}
          tickFormatter={formatShortDate}
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          width={72}
          tickFormatter={format}
        />
        <ChartTooltip
          content={({ active, label: date }) => {
            const p = active ? byDate.get(String(date)) : undefined
            if (!p) return null
            const series = p[dataKey]
            return (
              <div className='grid min-w-44 gap-1 rounded-lg border bg-background px-3 py-2 text-xs shadow-xl'>
                <p className='font-medium'>{formatShortDate(p.record_date)}</p>
                <p className='font-semibold tabular-nums'>
                  {label}: {series == null ? '—' : format(series)}
                </p>
                <p className='text-muted-foreground tabular-nums'>
                  That day: {format(p.value)}
                </p>
              </div>
            )
          }}
        />
        <Line
          type='monotone'
          dataKey={dataKey}
          stroke={`var(--color-${dataKey})`}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ChartContainer>
  )
}
