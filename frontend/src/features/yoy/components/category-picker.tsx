import { useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ChartControls } from '@/components/charts/chart-controls'
import type { CategoryList } from '@/features/lookups/api'
import type { ComparisonMode } from '../api'

export type TransactionFilter = 'all' | 'Deposits' | 'Withdrawals'

type CategoryPickerProps = {
  years: number[]
  categories: CategoryList | undefined
  currentFiscalYear: number
  previousFiscalYear: number
  comparisonMode: ComparisonMode
  transactionType: TransactionFilter
  selected: string[]
  onCurrentYearChange: (year: number) => void
  onPreviousYearChange: (year: number) => void
  onComparisonModeChange: (mode: ComparisonMode) => void
  onTransactionTypeChange: (type: TransactionFilter) => void
  onSelectedChange: (categories: string[]) => void
  onCompare: () => void
}

/** Category labels for a transaction-type filter, searched by substring. */
export function filterCategories(
  categories: CategoryList | undefined,
  type: TransactionFilter,
  search: string
): string[] {
  if (!categories) return []
  const deposits = categories.deposits ?? []
  const withdrawals = categories.withdrawals ?? []
  // The same label can be both a deposit and a withdrawal category.
  let list =
    type === 'Deposits'
      ? deposits
      : type === 'Withdrawals'
        ? withdrawals
        : [...new Set([...deposits, ...withdrawals])].sort()
  const q = search.trim().toLowerCase()
  if (q) list = list.filter((c) => c.toLowerCase().includes(q))
  return list
}

export function CategoryPicker(props: CategoryPickerProps) {
  const [search, setSearch] = useState('')
  const available = useMemo(
    () => filterCategories(props.categories, props.transactionType, search),
    [props.categories, props.transactionType, search]
  )
  const toggle = (category: string) =>
    props.onSelectedChange(
      props.selected.includes(category)
        ? props.selected.filter((c) => c !== category)
        : [...props.selected, category]
    )

  return (
    <Card>
      <CardHeader>
        <CardTitle>Configure the comparison</CardTitle>
        <CardDescription>
          Fiscal years, transaction type, and the Deposits &amp; Withdrawals
          categories to compare
        </CardDescription>
      </CardHeader>
      <CardContent className='flex flex-col gap-6'>
        <div className='flex flex-wrap items-end gap-4'>
          <ChartControls
            currentFiscalYear={props.currentFiscalYear}
            previousFiscalYear={props.previousFiscalYear}
            availableFiscalYears={props.years}
            onCurrentYearChange={props.onCurrentYearChange}
            onPreviousYearChange={props.onPreviousYearChange}
            comparisonMode={props.comparisonMode}
            onComparisonModeChange={props.onComparisonModeChange}
          />
          <div className='flex flex-col gap-2'>
            <Label htmlFor='transaction-type'>Transaction type</Label>
            <Select
              value={props.transactionType}
              onValueChange={(value) => {
                props.onTransactionTypeChange(value as TransactionFilter)
                // The category lists differ by type, so a selection may not carry over.
                props.onSelectedChange([])
              }}
            >
              <SelectTrigger id='transaction-type' className='w-40'>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value='all'>All</SelectItem>
                <SelectItem value='Deposits'>Deposits</SelectItem>
                <SelectItem value='Withdrawals'>Withdrawals</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className='flex flex-col gap-2'>
          <Label htmlFor='category-search'>
            Categories ({props.selected.length} selected)
          </Label>
          <Input
            id='category-search'
            placeholder='Search categories, e.g. Medicare, Defense, DHS'
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          {search && (
            <p className='text-xs text-muted-foreground'>
              {available.length} matching categories
            </p>
          )}
          <div className='max-h-64 overflow-y-auto rounded-md border p-3'>
            {available.length === 0 ? (
              <p className='py-4 text-center text-sm text-muted-foreground'>
                {props.categories
                  ? `No categories match "${search}".`
                  : 'Loading categories…'}
              </p>
            ) : (
              <div className='grid gap-1 md:grid-cols-2 lg:grid-cols-3'>
                {available.map((category) => (
                  <label
                    key={category}
                    className='flex cursor-pointer items-center gap-2 rounded p-1 text-sm hover:bg-muted/50'
                  >
                    <Checkbox
                      checked={props.selected.includes(category)}
                      onCheckedChange={() => toggle(category)}
                    />
                    <span className='truncate' title={category}>
                      {category}
                    </span>
                  </label>
                ))}
              </div>
            )}
          </div>
        </div>

        <Button
          className='w-fit'
          disabled={props.selected.length === 0}
          onClick={props.onCompare}
        >
          Compare categories
        </Button>
      </CardContent>
    </Card>
  )
}
