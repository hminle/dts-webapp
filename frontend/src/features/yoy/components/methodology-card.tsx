import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const SECTIONS: { title: string; items: React.ReactNode[] }[] = [
  {
    title: 'Data source',
    items: [
      <>
        The <code>deposits_withdrawals</code> table of the Daily Treasury
        Statement
      </>,
      <>
        Categories are its <code>transaction_catg</code> values
      </>,
    ],
  },
  {
    title: 'Alignment',
    items: [
      'Fiscal years are aligned by day of the fiscal year (the Nth business day with data)',
      'Day 1 is the first business day on or after October 1',
      'Only days with data in both years are compared',
    ],
  },
  {
    title: 'Amounts',
    items: [
      'Fiscal-year-to-date (FYTD) cumulative amounts',
      'Values in millions of dollars',
    ],
  },
  {
    title: 'Difference',
    items: [
      'YoY difference = current-year FYTD − previous-year FYTD',
      '% change = (current − previous) / |previous| × 100',
    ],
  },
]

export function MethodologyCard() {
  const [open, setOpen] = useState(false)
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <Button
            variant='ghost'
            className='-mx-3 w-[calc(100%+1.5rem)] justify-between'
            aria-expanded={open}
            onClick={() => setOpen(!open)}
          >
            Calculation methodology
            {open ? <ChevronUp /> : <ChevronDown />}
          </Button>
        </CardTitle>
      </CardHeader>
      {open && (
        <CardContent className='grid gap-4 text-sm md:grid-cols-2'>
          {SECTIONS.map((section) => (
            <div key={section.title} className='flex flex-col gap-1'>
              <h4 className='font-medium'>{section.title}</h4>
              <ul className='ms-4 list-disc text-muted-foreground'>
                {section.items.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </CardContent>
      )}
    </Card>
  )
}
