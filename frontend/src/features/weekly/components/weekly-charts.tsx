import {
  Bar,
  BarChart,
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
import { SERIES } from '@/lib/chart'
import { formatCurrency, formatTreasuryValue } from '@/lib/format'
import type { WeekRow } from '../lib'

type WeeklyChartsProps = {
  rows: WeekRow[]
  firstFiscalYear: number
  secondFiscalYear: number
}

const span = (fy: number) => `FY ${fy - 1}–${fy}`

const axes = (yLabel: string) => (
  <>
    <CartesianGrid vertical={false} />
    <XAxis
      dataKey='week'
      tickLine={false}
      axisLine={false}
      tickMargin={8}
      label={{
        value: 'Week of the fiscal year',
        position: 'bottom',
        offset: 8,
      }}
    />
    <YAxis
      tickLine={false}
      axisLine={false}
      width={72}
      // Millions in, so T / B / M out; the reference labelled billions as "K".
      tickFormatter={formatTreasuryValue}
      label={{ value: yLabel, angle: -90, position: 'insideLeft', offset: -2 }}
    />
  </>
)

export function WeeklyCharts({
  rows,
  firstFiscalYear,
  secondFiscalYear,
}: WeeklyChartsProps) {
  const barConfig = {
    firstFytd: { label: span(firstFiscalYear), color: SERIES.current },
    secondFytd: { label: span(secondFiscalYear), color: SERIES.previous },
  } satisfies ChartConfig
  const diffConfig = {
    difference: { label: 'Weekly difference', color: SERIES.current },
  } satisfies ChartConfig
  const labels: Record<string, string> = {
    firstFytd: barConfig.firstFytd.label,
    secondFytd: barConfig.secondFytd.label,
    difference: diffConfig.difference.label,
  }
  const tooltip = (
    <ChartTooltip
      content={
        <ChartTooltipContent
          labelFormatter={(_, payload) => `Week ${payload?.[0]?.payload?.week}`}
          formatter={(value, name) => (
            <div className='flex w-full justify-between gap-4'>
              <span className='text-muted-foreground'>
                {labels[String(name)] ?? name}
              </span>
              <span className='tabular-nums'>
                {formatCurrency(Number(value))}
              </span>
            </div>
          )}
        />
      }
    />
  )

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Weekly net government transfers, FYTD</CardTitle>
          <CardDescription>
            Read on each week's anchor day (or the closest earlier day with
            data) · millions of dollars
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={barConfig}
            className='aspect-auto h-[28rem] w-full'
          >
            <BarChart
              data={rows}
              margin={{ top: 8, right: 16, left: 8, bottom: 24 }}
            >
              {axes('Net transfers FYTD')}
              {tooltip}
              <ChartLegend
                content={<ChartLegendContent />}
                verticalAlign='top'
              />
              <Bar
                dataKey='firstFytd'
                fill='var(--color-firstFytd)'
                isAnimationActive={false}
              />
              <Bar
                dataKey='secondFytd'
                fill='var(--color-secondFytd)'
                isAnimationActive={false}
              />
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Weekly difference ({span(firstFiscalYear)} vs{' '}
            {span(secondFiscalYear)})
          </CardTitle>
          <CardDescription>
            Above zero means higher net transfers in FY {firstFiscalYear} than
            FY {secondFiscalYear}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={diffConfig}
            className='aspect-auto h-96 w-full'
          >
            <LineChart
              data={rows}
              margin={{ top: 8, right: 16, left: 8, bottom: 24 }}
            >
              {axes('Difference')}
              {tooltip}
              <ReferenceLine
                y={0}
                stroke='var(--muted-foreground)'
                strokeDasharray='3 3'
              />
              <Line
                type='monotone'
                dataKey='difference'
                stroke='var(--color-difference)'
                strokeWidth={2}
                dot={{ r: 2 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ChartContainer>
        </CardContent>
      </Card>
    </>
  )
}
