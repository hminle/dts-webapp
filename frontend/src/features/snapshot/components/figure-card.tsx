import { StatCard } from '@/components/stat-card'
import type { FormulaId } from '@/features/methodology/formulas'
import {
  changeClass,
  changeText,
  signedPrefix,
  totalText,
} from '@/features/yoy/components/accent'
import { formatPercent } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { SnapshotFigure } from '../api'

type FigureCardProps = {
  title: string
  figure: SnapshotFigure
  previousFiscalYear: number
  hint: FormulaId
}

/** One fiscal-year-to-date figure with its change from a year earlier. */
export function FigureCard({
  title,
  figure,
  previousFiscalYear,
  hint,
}: FigureCardProps) {
  return (
    <StatCard
      title={title}
      hint={hint}
      value={totalText(figure.current)}
      note={
        figure.previous === null ? (
          `No FY${previousFiscalYear} statement for this day`
        ) : (
          <>
            vs {totalText(figure.previous)} in FY{previousFiscalYear} ·{' '}
            <span
              className={cn(
                'font-medium tabular-nums',
                figure.change !== null && changeClass(figure.change)
              )}
            >
              {changeText(figure.change)}
              {figure.percent_change != null &&
                ` (${signedPrefix(figure.percent_change)}${formatPercent(figure.percent_change)})`}
            </span>
          </>
        )
      }
    />
  )
}
