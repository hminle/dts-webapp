import { useState } from 'react'
import { CircleAlert } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  AnchorWeekdaySelect,
  type AnchorWeekday,
} from '@/components/anchor-weekday-select'
import { FiscalYearSelect } from '@/components/fiscal-year-select'
import { QueryState } from '@/components/query-state'
import { useFiscalYears } from '@/features/lookups/api'
import { useWeeklyComparison } from './api'
import { SummaryStats } from './components/summary-stats'
import { WeeklyCharts } from './components/weekly-charts'
import { WeeklyTable } from './components/weekly-table'
import { computeSummaryStats, weekRows } from './lib'

export function WeeklyPage() {
  const years = useFiscalYears()
  const [chosenFirst, setChosenFirst] = useState<number | null>(null)
  const [chosenSecond, setChosenSecond] = useState<number | null>(null)
  const first = chosenFirst ?? years.data?.[0] ?? null
  const second = chosenSecond ?? years.data?.[1] ?? null
  const [anchor, setAnchor] = useState<AnchorWeekday>('friday')
  const comparison = useWeeklyComparison(first, second, anchor)

  return (
    <div className='flex flex-col gap-6'>
      <Card>
        <CardHeader>
          <CardTitle>Fiscal years to compare</CardTitle>
          <CardDescription>
            Net government transfers on each week's anchor day, or the
            closest earlier day with data
          </CardDescription>
        </CardHeader>
        <CardContent className='flex flex-wrap gap-6'>
          <FiscalYearSelect
            id='first-fiscal-year'
            label='First fiscal year'
            years={years.data ?? []}
            value={first}
            onChange={setChosenFirst}
          />
          <FiscalYearSelect
            id='second-fiscal-year'
            label='Second fiscal year'
            years={years.data ?? []}
            value={second}
            onChange={setChosenSecond}
          />
          <AnchorWeekdaySelect
            id='anchor-weekday'
            value={anchor}
            onChange={setAnchor}
          />
        </CardContent>
      </Card>

      {first !== null && first === second && (
        <Alert>
          <CircleAlert />
          <AlertDescription>
            Choose two different fiscal years to compare.
          </AlertDescription>
        </Alert>
      )}

      {first !== null && second !== null && first !== second && (
        <QueryState query={comparison} skeletonClassName='h-96'>
          {(data) => {
            const stats = computeSummaryStats(data)
            if (!stats) {
              return (
                <Alert>
                  <CircleAlert />
                  <AlertDescription>
                    FY {data.first_fiscal_year} has no {anchor} with data yet.
                  </AlertDescription>
                </Alert>
              )
            }
            const rows = weekRows(data)
            return (
              <>
                <SummaryStats data={data} stats={stats} />
                <WeeklyCharts
                  rows={rows}
                  firstFiscalYear={data.first_fiscal_year}
                  secondFiscalYear={data.second_fiscal_year}
                />
                <WeeklyTable
                  rows={rows}
                  weeks={data.comparison_weeks}
                  firstFiscalYear={data.first_fiscal_year}
                  secondFiscalYear={data.second_fiscal_year}
                />
              </>
            )
          }}
        </QueryState>
      )}
    </div>
  )
}
