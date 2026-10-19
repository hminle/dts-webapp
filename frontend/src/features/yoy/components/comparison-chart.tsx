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
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart'
import type { ChartConfig } from '@/components/ui/chart'
import { CHART_COLORS } from '@/lib/chart'
import { formatCurrency, formatTreasuryValue } from '@/lib/format'
import type { YoYCategoryComparison } from '../api'
import { categoryDiffSeries } from '../lib'

export function ComparisonChart({ data }: { data: YoYCategoryComparison }) {
  const categories = (data.current_year_data ?? []).map(
    (c) => c.category_description
  )
  // Category labels contain spaces and punctuation, which chart config keys and
  // CSS variables cannot; rows are re-keyed by index (c0, c1, …).
  const series = categoryDiffSeries(data).map((row) => {
    const keyed: Record<string, number> = { day: row.day }
    categories.forEach((label, i) => {
      if (label in row) keyed[`c${i}`] = row[label]
    })
    return keyed
  })
  if (series.length === 0) return null
  const config = Object.fromEntries(
    categories.map((label, i) => [
      `c${i}`,
      { label, color: CHART_COLORS[i % CHART_COLORS.length] },
    ])
  ) satisfies ChartConfig

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          YoY difference: FY{data.current_fiscal_year} − FY
          {data.previous_fiscal_year}
        </CardTitle>
        <CardDescription>
          Above zero means the current year is higher · {series.length} days
          compared · millions of dollars
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={config}
          className='aspect-auto h-[30rem] w-full'
        >
          <LineChart
            data={series}
            margin={{ top: 8, right: 16, left: 8, bottom: 24 }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey='day'
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
              // Amounts are millions; the reference formatted them as dollars,
              // so a trillion read "$1.00M".
              tickFormatter={formatTreasuryValue}
            />
            <ChartTooltip
              content={
                <ChartTooltipContent
                  labelFormatter={(_, payload) =>
                    `Day ${payload?.[0]?.payload?.day}`
                  }
                  formatter={(value, name) => (
                    <div className='flex w-full justify-between gap-4'>
                      <span className='text-muted-foreground'>
                        {config[name as keyof typeof config]?.label ?? name}
                      </span>
                      <span className='tabular-nums'>
                        {formatCurrency(Number(value))}
                      </span>
                    </div>
                  )}
                />
              }
            />
            <ChartLegend content={<ChartLegendContent />} />
            <ReferenceLine
              y={0}
              stroke='var(--muted-foreground)'
              strokeDasharray='3 3'
            />
            {categories.map((label, i) => (
              <Line
                key={label}
                type='monotone'
                dataKey={`c${i}`}
                stroke={`var(--color-c${i})`}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
