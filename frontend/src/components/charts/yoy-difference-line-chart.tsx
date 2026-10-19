import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  XAxis,
  YAxis,
} from 'recharts'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { ChartContainer, ChartTooltip } from '@/components/ui/chart'
import type { ChartConfig } from '@/components/ui/chart'
import type { ComparisonMode, YoYDailyDataPoint } from '@/features/yoy/api'
import { formatPercent, formatTreasuryValue } from '@/lib/format'
import { SERIES } from '@/lib/chart'
import { cn } from '@/lib/utils'

type YoYDifferenceLineChartProps = {
  title: string
  data: YoYDailyDataPoint[]
  currentFiscalYear: number
  previousFiscalYear: number
  comparisonMode: ComparisonMode
  comparisonDays?: number
  /** Chart height as a Tailwind class. */
  heightClassName?: string
  /** Line color; a CSS color or theme variable. */
  color?: string
  formatValue?: (value: number) => string
}

const signed = (value: number, format: (v: number) => string) =>
  `${value >= 0 ? '+' : ''}${format(value)}`

export function YoYDifferenceLineChart({
  title,
  data,
  currentFiscalYear,
  previousFiscalYear,
  comparisonMode,
  comparisonDays,
  heightClassName = 'h-[28rem]',
  color = SERIES.current,
  formatValue = formatTreasuryValue,
}: YoYDifferenceLineChartProps) {
  const config = {
    difference: { label: 'Change from year ago', color },
  } satisfies ChartConfig
  const byDay = new Map(data.map((p) => [p.day_of_fiscal_year, p]))
  const modeLabel =
    comparisonMode === 'calendar_date' ? 'by calendar date' : 'by fiscal day'

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>
          FY {currentFiscalYear} vs FY {previousFiscalYear} ({modeLabel})
          {comparisonDays ? ` · comparing ${comparisonDays} days` : ''}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={config}
          className={cn('aspect-auto w-full', heightClassName)}
        >
          <LineChart
            data={data}
            margin={{ top: 8, right: 16, left: 8, bottom: 24 }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey='day_of_fiscal_year'
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              label={{
                value: 'Day of fiscal year',
                position: 'bottom',
                offset: 8,
              }}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              width={72}
              tickFormatter={formatValue}
            />
            <ChartTooltip
              content={({ active, label }) => {
                const point = active ? byDay.get(Number(label)) : undefined
                if (!point) return null
                return (
                  <div className='grid min-w-48 gap-1 rounded-lg border bg-background px-3 py-2 text-xs shadow-xl'>
                    <p className='font-medium'>
                      Day {point.day_of_fiscal_year} ({point.current_date})
                    </p>
                    <p
                      className={cn(
                        'font-semibold tabular-nums',
                        point.difference >= 0
                          ? 'text-success'
                          : 'text-destructive'
                      )}
                    >
                      Change from year ago:{' '}
                      {signed(point.difference, formatValue)}
                      {point.percent_change != null &&
                        ` (${signed(point.percent_change, formatPercent)})`}
                    </p>
                    <p className='text-muted-foreground tabular-nums'>
                      FY {currentFiscalYear}: {formatValue(point.current_value)}
                    </p>
                    <p className='text-muted-foreground tabular-nums'>
                      FY {previousFiscalYear}:{' '}
                      {formatValue(point.previous_value)}
                      {comparisonMode === 'calendar_date' && point.previous_date
                        ? ` (${point.previous_date})`
                        : ''}
                    </p>
                  </div>
                )
              }}
            />
            <ReferenceLine
              y={0}
              stroke='var(--muted-foreground)'
              strokeWidth={1.5}
            />
            <Line
              type='monotone'
              dataKey='difference'
              stroke='var(--color-difference)'
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              isAnimationActive={false}
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
