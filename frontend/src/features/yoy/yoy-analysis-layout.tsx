import { useState, type ReactNode } from 'react'
import { CircleAlert } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ChartControls } from '@/components/charts/chart-controls'
import { YoYDifferenceLineChart } from '@/components/charts/yoy-difference-line-chart'
import { QueryState } from '@/components/query-state'
import { StatCard } from '@/components/stat-card'
import { useFiscalYears } from '@/features/lookups/api'
import { currentFiscalYear } from '@/lib/fiscal'
import { formatSignedPercent, formatTreasuryValue } from '@/lib/format'
import { useYoYDailyComparison } from './api'
import type { ComparisonMode, YearPair, YoYMetric } from './api'
import { changeClass, signedPrefix } from './components/accent'
import { summarize } from './lib'

type YoYAnalysisLayoutProps = {
  title: string
  description: string
  metric: YoYMetric
  /** A note above the controls, e.g. how the metric is calculated. */
  infoAlert?: ReactNode
  /** A caption under the latest-change card. */
  latestNote?: string
  /** Category cards shown between the summary and the chart. */
  renderCategoriesSection?: (pair: YearPair) => ReactNode
}

const signed = (value: number) =>
  `${signedPrefix(value)}${formatTreasuryValue(value)}`

export function YoYAnalysisLayout({
  title,
  description,
  metric,
  infoAlert,
  latestNote,
  renderCategoriesSection,
}: YoYAnalysisLayoutProps) {
  const years = useFiscalYears()
  // Null until the user chooses; default to the newest year with data.
  const [chosenCurrent, setChosenCurrent] = useState<number | null>(null)
  const [chosenPrevious, setChosenPrevious] = useState<number | null>(null)
  const [comparisonMode, setComparisonMode] =
    useState<ComparisonMode>('fiscal_day')
  const current = chosenCurrent ?? years.data?.[0] ?? currentFiscalYear()
  const previous = chosenPrevious ?? current - 1
  const pair: YearPair = {
    currentFiscalYear: current,
    previousFiscalYear: previous,
    comparisonMode,
  }
  const comparison = useYoYDailyComparison(pair, metric)

  return (
    <div className='flex flex-col gap-6'>
      <p className='text-sm text-muted-foreground'>{description}</p>
      {infoAlert}

      <ChartControls
        currentFiscalYear={current}
        previousFiscalYear={previous}
        availableFiscalYears={years.data ?? []}
        onCurrentYearChange={setChosenCurrent}
        onPreviousYearChange={setChosenPrevious}
        comparisonMode={comparisonMode}
        onComparisonModeChange={setComparisonMode}
      />

      {current === previous ? (
        <Alert>
          <CircleAlert />
          <AlertDescription>
            Choose two different fiscal years to compare.
          </AlertDescription>
        </Alert>
      ) : (
        <QueryState query={comparison} skeletonClassName='h-96'>
          {(data) => {
            const points = data.data_points ?? []
            const summary = summarize(points)
            if (!summary) {
              return (
                <Alert>
                  <CircleAlert />
                  <AlertDescription>
                    No days to compare for these years yet.
                  </AlertDescription>
                </Alert>
              )
            }
            return (
              <>
                <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
                  <StatCard
                    title='Latest YoY change'
                    value={signed(summary.latestDifference)}
                    valueClassName={changeClass(summary.latestDifference)}
                    note={
                      [
                        summary.latestPercentChange !== null
                          ? formatSignedPercent(summary.latestPercentChange)
                          : null,
                        latestNote,
                      ]
                        .filter(Boolean)
                        .join(' · ') || undefined
                    }
                  />
                  <StatCard
                    title='Average YoY change'
                    value={signed(summary.averageDifference)}
                    valueClassName={changeClass(summary.averageDifference)}
                  />
                  <StatCard
                    title='Largest YoY change'
                    value={signed(summary.maxDifference)}
                    valueClassName={changeClass(summary.maxDifference)}
                  />
                  <StatCard
                    title='Smallest YoY change'
                    value={signed(summary.minDifference)}
                    valueClassName={changeClass(summary.minDifference)}
                  />
                </div>

                {renderCategoriesSection?.(pair)}

                <YoYDifferenceLineChart
                  title={title}
                  data={points}
                  currentFiscalYear={current}
                  previousFiscalYear={previous}
                  comparisonMode={comparisonMode}
                  comparisonDays={data.comparison_days}
                />

                <div className='grid gap-4 md:grid-cols-2'>
                  <StatCard
                    title={`FY ${current} latest FYTD`}
                    value={formatTreasuryValue(summary.latestCurrentValue)}
                  />
                  <StatCard
                    title={`FY ${previous} at the same point`}
                    value={formatTreasuryValue(summary.latestPreviousValue)}
                  />
                </div>
              </>
            )
          }}
        </QueryState>
      )}
    </div>
  )
}
