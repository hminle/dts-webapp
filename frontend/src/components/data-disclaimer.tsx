import { Link } from '@tanstack/react-router'

const LINK = 'underline underline-offset-2 hover:text-foreground'

export function DataDisclaimer() {
  return (
    <p className='px-2 py-1 text-xs text-muted-foreground group-data-[collapsible=icon]:hidden'>
      Not financial advice · Source: U.S. Treasury ·{' '}
      <Link to='/terms' className={LINK}>
        Terms
      </Link>{' '}
      ·{' '}
      <Link to='/privacy' className={LINK}>
        Privacy
      </Link>
    </p>
  )
}
