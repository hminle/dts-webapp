/** The U.S. federal fiscal year containing `today`; October starts the next one. */
export function currentFiscalYear(today: Date = new Date()): number {
  return today.getMonth() >= 9 ? today.getFullYear() + 1 : today.getFullYear()
}
