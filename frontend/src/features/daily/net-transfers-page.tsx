import { useState } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { FiscalYearSelect } from '@/components/fiscal-year-select'
import { QueryState } from '@/components/query-state'
import { useFiscalYears } from '@/features/lookups/api'
import { useNetTransfersForFiscalYear } from './api'
import { FiscalYearTable } from './components/fiscal-year-table'

function YearColumn({ year }: { year: number | null }) {
  const days = useNetTransfersForFiscalYear(year)
  return (
    <Card className='min-w-0'>
      <CardHeader>
        <CardTitle>{year ? `FY ${year}` : 'Choose a fiscal year'}</CardTitle>
        <CardDescription>
          {days.data ? `${days.data.length} days of data` : 'Daily net transfers'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {year && (
          <QueryState query={days} skeletonClassName='h-64'>
            {(data) => <FiscalYearTable days={data} />}
          </QueryState>
        )}
      </CardContent>
    </Card>
  )
}

export function NetTransfersComparePage() {
  const years = useFiscalYears()
  // Unset until the user picks; defaults come from the newest two years.
  const [first, setFirst] = useState<number | null>(null)
  const [second, setSecond] = useState<number | null>(null)
  const available = years.data ?? []
  const firstYear = first ?? available[0] ?? null
  const secondYear = second ?? available[1] ?? null

  return (
    <div className='flex flex-col gap-6'>
      <Card>
        <CardHeader>
          <CardTitle>Compare fiscal years</CardTitle>
          <CardDescription>
            Daily net transfers side by side · millions of dollars
          </CardDescription>
        </CardHeader>
        <CardContent className='flex flex-wrap gap-6'>
          <FiscalYearSelect
            id='first-fiscal-year'
            label='First fiscal year'
            years={available}
            value={firstYear}
            onChange={setFirst}
          />
          <FiscalYearSelect
            id='second-fiscal-year'
            label='Second fiscal year'
            years={available}
            value={secondYear}
            onChange={setSecond}
          />
        </CardContent>
      </Card>

      <div className='grid gap-4 lg:grid-cols-2'>
        <YearColumn year={firstYear} />
        <YearColumn year={secondYear} />
      </div>
    </div>
  )
}
