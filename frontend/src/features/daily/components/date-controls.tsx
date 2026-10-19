import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

type DateControlsProps = {
  initialDate: string
  onSearch: (date: string) => void
}

export function DateControls({ initialDate, onSearch }: DateControlsProps) {
  const [date, setDate] = useState(initialDate)

  return (
    <form
      className='flex flex-wrap items-end gap-3'
      onSubmit={(event) => {
        event.preventDefault()
        if (date) onSearch(date)
      }}
    >
      <div className='flex flex-col gap-2'>
        <Label htmlFor='statement-date'>Date</Label>
        <Input
          id='statement-date'
          type='date'
          className='w-44'
          value={date}
          onChange={(event) => setDate(event.target.value)}
        />
      </div>
      <Button type='submit'>Search</Button>
    </form>
  )
}
