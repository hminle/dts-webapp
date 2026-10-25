import {
  BarChart3,
  BookOpen,
  CalendarDays,
  CalendarRange,
  Database,
  Landmark,
  LayoutDashboard,
  Newspaper,
  TrendingUp,
} from 'lucide-react'
import { type NavItem, type NavLink } from '../types'

export const MENU_ITEMS: NavItem[] = [
  { title: 'Overview', url: '/', icon: LayoutDashboard },
  { title: 'Weekly snapshot', url: '/snapshot', icon: Newspaper },
  {
    title: 'Daily',
    icon: CalendarDays,
    items: [
      { title: 'Single date', url: '/daily/single-date' },
      { title: 'Net transfers', url: '/daily/net-transfers' },
      { title: 'Leading flows', url: '/daily/leading-flows' },
    ],
  },
  { title: 'Fiscal year', url: '/fiscal-year', icon: BarChart3 },
  {
    title: 'Year over year',
    icon: TrendingUp,
    items: [
      { title: 'Net transfers', url: '/yoy/net-transfers' },
      { title: 'Withdrawals', url: '/yoy/withdrawals' },
      { title: 'Deposits', url: '/yoy/deposits' },
      { title: 'Category comparison', url: '/yoy/categories' },
    ],
  },
  { title: 'Weekly comparison', url: '/weekly', icon: CalendarRange },
  { title: 'Cash balance', url: '/cash-balance', icon: Landmark },
]

/** Pinned under the menu: about the data rather than views of it. */
export const FOOTER_ITEMS: NavLink[] = [
  { title: 'Data status', url: '/data-status', icon: Database },
  { title: 'Methodology', url: '/methodology', icon: BookOpen },
]
