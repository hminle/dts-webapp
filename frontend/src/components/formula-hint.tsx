import { Link } from '@tanstack/react-router'
import { CircleHelp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Popover,
  PopoverContent,
  PopoverDescription,
  PopoverHeader,
  PopoverTitle,
  PopoverTrigger,
} from '@/components/ui/popover'
import { FORMULAS, type FormulaId } from '@/features/methodology/formulas'
import { cn } from '@/lib/utils'

/** A "How is this calculated?" button that opens a formula from the registry. */
export function FormulaHint({
  id,
  className,
}: {
  id: FormulaId
  className?: string
}) {
  const formula = FORMULAS[id]
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant='ghost'
          size='icon-xs'
          className={cn('text-muted-foreground', className)}
          aria-label={`${formula.title}: how is this calculated?`}
        >
          <CircleHelp />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        collisionPadding={16}
        className='w-80 max-w-[calc(100vw-2rem)]'
      >
        <PopoverHeader>
          <PopoverTitle>{formula.title}</PopoverTitle>
          <PopoverDescription>{formula.summary}</PopoverDescription>
        </PopoverHeader>
        <div className='flex flex-col gap-1 rounded bg-muted/40 p-2 font-mono text-xs'>
          {formula.expression.map((line) => (
            <p key={line}>{line}</p>
          ))}
        </div>
        <Link
          to='/methodology'
          hash={id}
          className='text-sm underline underline-offset-4 hover:text-muted-foreground'
        >
          Read the full explanation
        </Link>
      </PopoverContent>
    </Popover>
  )
}
