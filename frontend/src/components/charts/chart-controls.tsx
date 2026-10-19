import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { FiscalYearSelect } from '@/components/fiscal-year-select'
import type { ComparisonMode } from '@/features/yoy/api'

type ChartControlsProps = {
  currentFiscalYear: number
  previousFiscalYear: number
  availableFiscalYears: number[]
  onCurrentYearChange: (year: number) => void
  onPreviousYearChange: (year: number) => void
  comparisonMode: ComparisonMode
  onComparisonModeChange: (mode: ComparisonMode) => void
}

// Fiscal day pairs day N with day N; calendar date pairs Dec 31 with Dec 31.
export const COMPARISON_MODE_LABELS: Record<ComparisonMode, string> = {
  fiscal_day: 'Fiscal day',
  calendar_date: 'Calendar date',
}

export function ChartControls({
  currentFiscalYear,
  previousFiscalYear,
  availableFiscalYears,
  onCurrentYearChange,
  onPreviousYearChange,
  comparisonMode,
  onComparisonModeChange,
}: ChartControlsProps) {
  return (
    <div className='flex flex-wrap items-end gap-4'>
      <FiscalYearSelect
        id='current-year'
        label='Current year'
        years={availableFiscalYears}
        value={currentFiscalYear}
        onChange={onCurrentYearChange}
      />
      <FiscalYearSelect
        id='previous-year'
        label='Previous year'
        years={availableFiscalYears}
        value={previousFiscalYear}
        onChange={onPreviousYearChange}
      />
      <div className='flex flex-col gap-2'>
        <Label htmlFor='comparison-mode'>Compare by</Label>
        <Select
          value={comparisonMode}
          onValueChange={(value) =>
            onComparisonModeChange(value as ComparisonMode)
          }
        >
          <SelectTrigger id='comparison-mode' className='w-44'>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(COMPARISON_MODE_LABELS) as ComparisonMode[]).map(
              (mode) => (
                <SelectItem key={mode} value={mode}>
                  {COMPARISON_MODE_LABELS[mode]}
                </SelectItem>
              )
            )}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
