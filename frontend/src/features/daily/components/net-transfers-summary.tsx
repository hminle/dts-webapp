import { useState } from 'react'
import { Link } from '@tanstack/react-router'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { FormulaHint } from '@/components/formula-hint'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { FormulaId } from '@/features/methodology/formulas'
import { formatCurrency, formatDate } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { DailyNetTransfer } from '../api'
import { FLOW_LABELS, flowDirection, formulaSteps } from '../lib'

const FLOW_CLASS = {
  outflow: 'text-success',
  inflow: 'text-destructive',
  balanced: '',
} as const

function Metric({
  label,
  value,
  note,
  hint,
  colored = false,
}: {
  label: string
  value: number
  note: string
  hint: FormulaId
  colored?: boolean
}) {
  return (
    <div className='flex flex-col gap-1 rounded-lg bg-muted/50 p-4'>
      <div className='flex items-center gap-1'>
        <p className='text-sm font-medium text-muted-foreground'>{label}</p>
        <FormulaHint id={hint} />
      </div>
      <p
        className={cn(
          'text-2xl font-semibold tabular-nums',
          colored && FLOW_CLASS[flowDirection(value)]
        )}
      >
        {formatCurrency(value)}
      </p>
      <p className='text-xs text-muted-foreground'>{note}</p>
    </div>
  )
}

export function NetTransfersSummary({ day }: { day: DailyNetTransfer }) {
  const [showCalculation, setShowCalculation] = useState(false)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Flow summary for {formatDate(day.record_date)}</CardTitle>
        <CardDescription>
          FY {day.record_fiscal_year} · Day {day.day_of_fiscal_year} of the
          fiscal year · millions of dollars
        </CardDescription>
      </CardHeader>
      <CardContent className='flex flex-col gap-4'>
        <div className='grid gap-4 md:grid-cols-3'>
          <Metric
            label='Net flow (today)'
            value={day.net_flow_today}
            note={FLOW_LABELS[flowDirection(day.net_flow_today)]}
            hint='net-transfers'
            colored
          />
          <Metric
            label='Leading flow'
            value={day.leading_flow}
            note='Total withdrawals (today)'
            hint='leading-flow'
          />
          <Metric
            label='Net flow (FYTD)'
            value={day.net_flow_fytd}
            note='Fiscal year to date'
            hint='today-mtd-fytd'
            colored
          />
        </div>

        <div className='grid gap-4 md:grid-cols-2'>
          <div className='flex flex-col gap-1'>
            <div className='flex items-center gap-1'>
              <p className='text-sm font-medium'>Total deposits (today)</p>
              <FormulaHint id='total-deposits' />
            </div>
            <p className='text-lg tabular-nums'>
              {formatCurrency(day.total_deposits_today)}
            </p>
          </div>
          <div className='flex flex-col gap-1'>
            <div className='flex items-center gap-1'>
              <p className='text-sm font-medium'>Total withdrawals (today)</p>
              <FormulaHint id='total-withdrawals' />
            </div>
            <p className='text-lg tabular-nums'>
              {formatCurrency(day.total_withdrawals_today)}
            </p>
          </div>
        </div>

        <div className='border-t pt-3'>
          <Button
            variant='ghost'
            className='w-full justify-between'
            aria-expanded={showCalculation}
            onClick={() => setShowCalculation(!showCalculation)}
          >
            How are these numbers calculated?
            {showCalculation ? <ChevronUp /> : <ChevronDown />}
          </Button>

          {showCalculation && (
            <div className='mt-3 flex flex-col gap-4 rounded-lg bg-muted/40 p-4 text-sm'>
              <p className='text-muted-foreground'>
                Debt management is filtered out to show the operating position:
                new borrowing is not revenue, and repaying maturing debt is not
                spending.
              </p>
              {formulaSteps(day).map((step) => (
                <div
                  key={step.title}
                  className='flex flex-col gap-1 border-l-2 pl-3'
                >
                  <p className='font-medium'>{step.title}</p>
                  <p className='text-muted-foreground'>{step.formula}</p>
                  <p className='rounded bg-background p-2 font-mono text-xs tabular-nums'>
                    {formatCurrency(step.values[0])} ={' '}
                    {formatCurrency(step.values[1])} −{' '}
                    {formatCurrency(step.values[2])}
                  </p>
                </div>
              ))}
              <ul className='ms-4 list-disc text-xs text-muted-foreground'>
                <li>
                  Positive net flow: the government spent more than it took in.
                </li>
                <li>Negative net flow: it took in more than it spent.</li>
                <li>
                  Leading flow equals total withdrawals, excluding debt
                  redemptions.
                </li>
              </ul>
              <Link
                to='/methodology'
                hash='surplus-or-deficit'
                className='underline underline-offset-4 hover:text-muted-foreground'
              >
                Read the full explanation
              </Link>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
