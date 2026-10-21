import type { ReactNode } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { FORMULAS } from '../formulas'
import type { FormulaId } from '../formulas'

/**
 * One formula from the registry: its expression, the terms it uses, an
 * optional worked example, and the mistakes readers usually make. The heading
 * carries the formula id, so `/methodology#<id>` lands on it.
 */
export function FormulaBlock({
  id,
  example,
  termLabels = ['Term', 'Meaning'],
}: {
  id: FormulaId
  example?: ReactNode
  /** Column headings for the terms table. */
  termLabels?: [string, string]
}) {
  const formula = FORMULAS[id]
  return (
    <div className='flex flex-col gap-3'>
      <h3 id={id} className='scroll-mt-20 font-medium text-foreground'>
        {formula.title}
      </h3>
      <div className='flex flex-col gap-1 rounded-lg bg-muted/40 p-4 font-mono text-sm text-foreground'>
        {formula.expression.map((line) => (
          <p key={line}>{line}</p>
        ))}
      </div>
      {formula.terms && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{termLabels[0]}</TableHead>
              <TableHead>{termLabels[1]}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {formula.terms.map(({ term, meaning }, i) => (
              <TableRow key={`${term}-${meaning}`}>
                {/* A group listed over several line items is named once. */}
                <TableCell className='font-medium whitespace-normal'>
                  {formula.terms?.[i - 1]?.term === term ? '' : term}
                </TableCell>
                <TableCell className='whitespace-normal'>{meaning}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      {example}
      {formula.pitfalls && (
        <div className='flex flex-col gap-1'>
          <p className='font-medium text-foreground'>Common mistakes</p>
          <ul className='flex flex-col gap-1'>
            {formula.pitfalls.map((pitfall) => (
              <li key={pitfall}>{pitfall}</li>
            ))}
          </ul>
        </div>
      )}
      <p className='text-xs'>Source: {formula.source}</p>
    </div>
  )
}
