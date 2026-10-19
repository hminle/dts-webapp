import type { DailyNetTransfer } from './api'

export type FlowDirection = 'outflow' | 'inflow' | 'balanced'

/** Net flow is withdrawals minus deposits: positive means more went out. */
export function flowDirection(netFlow: number): FlowDirection {
  if (netFlow > 0) return 'outflow'
  if (netFlow < 0) return 'inflow'
  return 'balanced'
}

export const FLOW_LABELS: Record<FlowDirection, string> = {
  outflow: 'Net Outflow (Deficit)',
  inflow: 'Net Inflow (Surplus)',
  balanced: 'Balanced',
}

export type FormulaStep = {
  title: string
  formula: string
  /** [result, left operand, right operand] in millions of dollars. */
  values: [number, number, number]
}

/** The three subtractions behind the summary, with the day's numbers. */
export function formulaSteps(day: DailyNetTransfer): FormulaStep[] {
  return [
    {
      title: 'Step 1: Total deposits',
      formula: 'Total Deposits = TGA Total Deposits − Public Debt Cash Issues',
      values: [
        day.total_deposits_today,
        day.tga_total_deposits_today,
        day.public_debt_issues_today,
      ],
    },
    {
      title: 'Step 2: Total withdrawals',
      formula: 'Total Withdrawals = TGA Total Withdrawals − Public Debt Cash Redemptions',
      values: [
        day.total_withdrawals_today,
        day.tga_total_withdrawals_today,
        day.public_debt_redemptions_today,
      ],
    },
    {
      title: 'Step 3: Net government transfers',
      formula: 'Net Flow = Total Withdrawals − Total Deposits',
      values: [day.net_flow_today, day.total_withdrawals_today, day.total_deposits_today],
    },
  ]
}
