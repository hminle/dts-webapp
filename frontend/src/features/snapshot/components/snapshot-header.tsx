import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { WeeklySnapshot } from '../api'
import { snapshotHeading } from '../lib'

/** Which statement the snapshot reads, and what it is compared with. */
export function SnapshotHeader({ snapshot }: { snapshot: WeeklySnapshot }) {
  const { title, holidayNote } = snapshotHeading(snapshot)
  const day = snapshot.day_of_fiscal_year
  return (
    <Card>
      <CardHeader>
        <CardTitle>Week ending {title}</CardTitle>
        <CardDescription>
          FY{snapshot.fiscal_year}, day {day} · compared with{' '}
          {snapshot.previous_date ?? 'no statement'} (FY
          {snapshot.previous_fiscal_year}, day {day})
        </CardDescription>
        {holidayNote && <CardDescription>{holidayNote}</CardDescription>}
      </CardHeader>
    </Card>
  )
}
