import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

type FiscalYearSelectProps = {
  id: string
  label: string
  years: number[]
  value: number | null
  onChange: (year: number) => void
}

export function FiscalYearSelect({
  id,
  label,
  years,
  value,
  onChange,
}: FiscalYearSelectProps) {
  return (
    <div className='flex flex-col gap-2'>
      <Label htmlFor={id}>{label}</Label>
      <Select
        value={value === null ? undefined : String(value)}
        onValueChange={(next) => onChange(Number(next))}
      >
        <SelectTrigger id={id} className='w-40'>
          <SelectValue placeholder='Choose a year' />
        </SelectTrigger>
        <SelectContent>
          {years.map((year) => (
            <SelectItem key={year} value={String(year)}>
              FY {year}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
