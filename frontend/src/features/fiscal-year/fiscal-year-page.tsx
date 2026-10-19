import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { FiscalYearSelect } from '@/components/fiscal-year-select'
import { QueryState } from '@/components/query-state'
import { dataSourceName, useDataSources, useFiscalYears } from '@/features/lookups/api'
import { formatNumber } from '@/lib/format'
import { useFiscalYearData } from './api'
import { ResultsGrid } from './components/results-grid'

const PAGE_SIZE = 50

export function FiscalYearPage() {
  const years = useFiscalYears()
  const sources = useDataSources()
  const [chosenYear, setChosenYear] = useState<number | null>(null)
  const [dataSource, setDataSource] = useState('all')
  const [page, setPage] = useState(1)
  const fiscalYear = chosenYear ?? years.data?.[0] ?? null
  const data = useFiscalYearData(
    fiscalYear === null ? null : { fiscalYear, dataSource, page, pageSize: PAGE_SIZE }
  )

  return (
    <div className='flex flex-col gap-6'>
      <Card>
        <CardHeader>
          <CardTitle>Fiscal year and source</CardTitle>
          <CardDescription>
            Every row the Treasury published for a fiscal year
          </CardDescription>
        </CardHeader>
        <CardContent className='flex flex-wrap gap-6'>
          <FiscalYearSelect
            id='fiscal-year'
            label='Fiscal year'
            years={years.data ?? []}
            value={fiscalYear}
            onChange={(year) => {
              setChosenYear(year)
              setPage(1)
            }}
          />
          <div className='flex flex-col gap-2'>
            <Label htmlFor='data-source'>Data source</Label>
            <Select
              value={dataSource}
              onValueChange={(value) => {
                setDataSource(value)
                setPage(1)
              }}
            >
              <SelectTrigger id='data-source' className='w-64'>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value='all'>All data sources</SelectItem>
                {(sources.data ?? []).map((source) => (
                  <SelectItem key={source} value={source}>
                    {dataSourceName(source)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {fiscalYear !== null && (
        <QueryState query={data} skeletonClassName='h-96'>
          {(result) => (
            <Card>
              <CardHeader>
                <CardTitle>
                  FY {fiscalYear}
                  {dataSource !== 'all' && (
                    <span className='ms-2 font-normal text-muted-foreground'>
                      · {dataSourceName(dataSource)}
                    </span>
                  )}
                </CardTitle>
                <CardDescription>
                  {formatNumber(result.total)} rows · page {result.page} of{' '}
                  {Math.max(result.pages, 1)} · newest first · millions of dollars
                </CardDescription>
              </CardHeader>
              <CardContent className='flex flex-col gap-3'>
                <ResultsGrid rows={result.items} />
                {result.pages > 1 && (
                  <div className='flex items-center justify-end gap-2'>
                    <Button
                      variant='outline'
                      size='sm'
                      disabled={page === 1}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                    >
                      Previous
                    </Button>
                    <Button
                      variant='outline'
                      size='sm'
                      disabled={page >= result.pages}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      Next
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </QueryState>
      )}
    </div>
  )
}
