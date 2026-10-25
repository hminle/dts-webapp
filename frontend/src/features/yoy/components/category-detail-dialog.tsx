import { TrendingDown, TrendingUp } from 'lucide-react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  XAxis,
  YAxis,
} from 'recharts'
import { Card, CardContent } from '@/components/ui/card'
import { ChartContainer, ChartTooltip } from '@/components/ui/chart'
import type { ChartConfig } from '@/components/ui/chart'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { FormulaHint } from '@/components/formula-hint'
import { QueryState } from '@/components/query-state'
import {
  formatBillions,
  formatDate,
  formatPercent,
  formatSignedPercent,
} from '@/lib/format'
import { cn } from '@/lib/utils'
import { useCategoryDailyYoY } from '../api'
import type { YearPair } from '../api'
import { breakdownRows } from '../lib'
import type { CategoryCardData } from '../lib'
import {
  ACCENT,
  changeClass,
  changeText,
  signedPrefix,
  totalText,
} from './accent'
import { BreakdownTable } from './breakdown-table'

const EXPLANATIONS: Partial<Record<CategoryCardData['categoryType'], string>> =
  {
    tbill:
      'T-Bill Interest comes from the adjustment_public_debt table (Table III-B): the discount on new debt issues.',
    irs_refund:
      'IRS Tax Refunds come from the income_tax_refunds table (Table V): EFT and check refunds to individuals and businesses.',
  }

type CategoryDetailDialogProps = {
  category: CategoryCardData | null
  pair: YearPair
  onClose: () => void
}

function Stat({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <Card>
      <CardContent className='flex flex-col gap-1'>
        <p className='text-sm text-muted-foreground'>{label}</p>
        {children}
      </CardContent>
    </Card>
  )
}

export function CategoryDetailDialog({
  category,
  pair,
  onClose,
}: CategoryDetailDialogProps) {
  const daily = useCategoryDailyYoY(
    pair,
    category ? { name: category.name, type: category.categoryType } : null
  )
  const { currentFiscalYear, previousFiscalYear, comparisonMode } = pair
  const config = {
    yoy_change: {
      label: 'YoY change',
      color: category ? ACCENT[category.accent].line : '',
    },
  } satisfies ChartConfig

  return (
    <Dialog
      open={category !== null}
      onOpenChange={(open) => !open && onClose()}
    >
      {category && (
        <DialogContent className='max-h-[90vh] overflow-y-auto sm:max-w-3xl'>
          <DialogHeader>
            <div className='flex items-center gap-1'>
              <DialogTitle>{category.name}</DialogTitle>
              <FormulaHint id={category.formula} />
            </div>
            <DialogDescription>
              FY{currentFiscalYear} vs FY{previousFiscalYear} (
              {comparisonMode === 'calendar_date'
                ? 'by calendar date'
                : 'by fiscal day'}
              ) · billions of dollars
            </DialogDescription>
          </DialogHeader>

          <div className='grid grid-cols-2 gap-3'>
            <Stat label={`FY${currentFiscalYear} FYTD`}>
              <p className='text-2xl font-semibold tabular-nums'>
                {totalText(category.current_fytd)}
              </p>
            </Stat>
            <Stat label={`FY${previousFiscalYear} FYTD`}>
              <p className='text-2xl font-semibold tabular-nums'>
                {totalText(category.previous_fytd)}
              </p>
            </Stat>
            <Stat label='YoY change'>
              <p
                className={cn(
                  'flex items-center gap-2 text-2xl font-semibold tabular-nums',
                  category.yoy_change !== null &&
                    changeClass(category.yoy_change)
                )}
              >
                {category.yoy_change !== null &&
                  (category.yoy_change >= 0 ? (
                    <TrendingUp />
                  ) : (
                    <TrendingDown />
                  ))}
                {changeText(category.yoy_change)}
              </p>
            </Stat>
            <Stat label='Percent change'>
              <p
                className={cn(
                  'text-2xl font-semibold tabular-nums',
                  category.yoy_percent_change !== null &&
                    changeClass(category.yoy_percent_change)
                )}
              >
                {category.yoy_percent_change !== null
                  ? formatSignedPercent(category.yoy_percent_change)
                  : 'N/A'}
              </p>
            </Stat>
          </div>

          {(category.current_fytd === null ||
            category.previous_fytd === null) && (
            <p className='text-sm text-muted-foreground'>
              This category is comparable from{' '}
              {formatDate(category.availableFrom)}. The Treasury reorganized
              its lines before that date.
            </p>
          )}

          {breakdownRows(category).length > 0 && (
            <section className='flex flex-col gap-2'>
              <h3 className='font-medium'>How this category is calculated</h3>
              {EXPLANATIONS[category.categoryType] && (
                <p className='text-sm text-muted-foreground'>
                  {EXPLANATIONS[category.categoryType]}
                </p>
              )}
              <BreakdownTable
                rows={breakdownRows(category)}
                total={{
                  current: category.current_fytd,
                  previous: category.previous_fytd,
                  change: category.yoy_change,
                }}
                currentFiscalYear={currentFiscalYear}
                previousFiscalYear={previousFiscalYear}
              />
            </section>
          )}

          <section className='flex flex-col gap-2'>
            <h3 className='font-medium'>Year-over-year change</h3>
            <QueryState query={daily} skeletonClassName='h-72'>
              {(result) => {
                const points = result.data_points ?? []
                if (points.length === 0) {
                  return (
                    <p className='py-8 text-center text-sm text-muted-foreground'>
                      No daily data for this category.
                    </p>
                  )
                }
                const byDay = new Map(
                  points.map((p) => [p.day_of_fiscal_year, p])
                )
                return (
                  <ChartContainer
                    config={config}
                    className='aspect-auto h-72 w-full'
                  >
                    <LineChart
                      data={points}
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
                        tickFormatter={formatBillions}
                      />
                      <ChartTooltip
                        content={({ active, label }) => {
                          const p = active
                            ? byDay.get(Number(label))
                            : undefined
                          if (!p) return null
                          return (
                            <div className='grid min-w-44 gap-1 rounded-lg border bg-background px-3 py-2 text-xs shadow-xl'>
                              <p className='font-medium'>
                                Day {p.day_of_fiscal_year} ({p.current_date})
                              </p>
                              <p
                                className={cn(
                                  'font-semibold tabular-nums',
                                  p.yoy_change !== null &&
                                    changeClass(p.yoy_change)
                                )}
                              >
                                YoY change: {changeText(p.yoy_change)}
                                {p.yoy_percent_change != null &&
                                  ` (${signedPrefix(p.yoy_percent_change)}${formatPercent(p.yoy_percent_change)})`}
                              </p>
                              <p className='text-muted-foreground tabular-nums'>
                                FY {currentFiscalYear}:{' '}
                                {totalText(p.current_fytd)}
                              </p>
                              <p className='text-muted-foreground tabular-nums'>
                                FY {previousFiscalYear}:{' '}
                                {totalText(p.previous_fytd)}
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
                        dataKey='yoy_change'
                        stroke='var(--color-yoy_change)'
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ChartContainer>
                )
              }}
            </QueryState>
          </section>
        </DialogContent>
      )}
    </Dialog>
  )
}
