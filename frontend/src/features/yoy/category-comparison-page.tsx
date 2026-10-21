import { useState } from 'react'
import { Link } from '@tanstack/react-router'
import { CircleAlert } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { QueryState } from '@/components/query-state'
import { useCategories, useFiscalYears } from '@/features/lookups/api'
import { currentFiscalYear } from '@/lib/fiscal'
import { useYoYCategoryComparison } from './api'
import type { CategoryComparisonQuery, ComparisonMode } from './api'
import { CategoryPicker } from './components/category-picker'
import type { TransactionFilter } from './components/category-picker'
import { ComparisonChart } from './components/comparison-chart'
import { ComparisonTable } from './components/comparison-table'

export function CategoryComparisonPage() {
  const years = useFiscalYears()
  const categories = useCategories()
  const [chosenCurrent, setChosenCurrent] = useState<number | null>(null)
  const [chosenPrevious, setChosenPrevious] = useState<number | null>(null)
  const [comparisonMode, setComparisonMode] =
    useState<ComparisonMode>('fiscal_day')
  const [transactionType, setTransactionType] =
    useState<TransactionFilter>('all')
  const [selected, setSelected] = useState<string[]>([])
  // The comparison runs only when the user presses Compare.
  const [query, setQuery] = useState<CategoryComparisonQuery | null>(null)
  const comparison = useYoYCategoryComparison(query)

  const current = chosenCurrent ?? years.data?.[0] ?? currentFiscalYear()
  const previous = chosenPrevious ?? current - 1
  const sameYear = current === previous

  return (
    <div className='flex flex-col gap-6'>
      <p className='text-sm text-muted-foreground'>
        Compare FYTD amounts of specific Deposits &amp; Withdrawals categories
        across two fiscal years.
      </p>

      <CategoryPicker
        years={years.data ?? []}
        categories={categories.data}
        currentFiscalYear={current}
        previousFiscalYear={previous}
        comparisonMode={comparisonMode}
        transactionType={transactionType}
        selected={selected}
        onCurrentYearChange={setChosenCurrent}
        onPreviousYearChange={setChosenPrevious}
        onComparisonModeChange={setComparisonMode}
        onTransactionTypeChange={setTransactionType}
        onSelectedChange={setSelected}
        onCompare={() =>
          // A same-year query is disabled and would never settle; the alert below
          // already says why nothing happens.
          !sameYear &&
          setQuery({
            currentFiscalYear: current,
            previousFiscalYear: previous,
            comparisonMode,
            categories: selected,
            transactionType:
              transactionType === 'all' ? undefined : transactionType,
          })
        }
      />

      {sameYear && (
        <Alert>
          <CircleAlert />
          <AlertDescription>
            Choose two different fiscal years to compare.
          </AlertDescription>
        </Alert>
      )}

      <Link
        to='/methodology'
        hash='any-line-item'
        className='text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground'
      >
        How this comparison is calculated
      </Link>

      {query && (
        <QueryState query={comparison} skeletonClassName='h-96'>
          {(data) => (
            <>
              <ComparisonChart data={data} />
              <ComparisonTable data={data} />
            </>
          )}
        </QueryState>
      )}
    </div>
  )
}
