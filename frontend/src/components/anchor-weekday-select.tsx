import { Label } from '@/components/ui/label'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'

export type AnchorWeekday = 'thursday' | 'friday'

type AnchorWeekdaySelectProps = {
  id: string
  value: AnchorWeekday
  onChange: (weekday: AnchorWeekday) => void
}

/** Thursday or Friday: the weekday each week is read on. */
export function AnchorWeekdaySelect({
  id,
  value,
  onChange,
}: AnchorWeekdaySelectProps) {
  return (
    <div className='flex flex-col gap-2'>
      <Label id={`${id}-label`}>Week ends on</Label>
      <ToggleGroup
        type='single'
        variant='outline'
        aria-labelledby={`${id}-label`}
        value={value}
        // A toggle group can deselect its item; keep the weekday instead.
        onValueChange={(next) => next && onChange(next as AnchorWeekday)}
      >
        <ToggleGroupItem value='thursday'>Thursday</ToggleGroupItem>
        <ToggleGroupItem value='friday'>Friday</ToggleGroupItem>
      </ToggleGroup>
    </div>
  )
}
