/**
 * Column preset shared by every data grid in the app: figures and the row-action
 * gutter both sit against the trailing edge, so they line up wherever they show.
 *
 * ReUI's grid puts `meta.headerClassName` on the `<th>` and `meta.cellClassName`
 * on the `<td>`. A sortable header renders a flex wrapper inside that `<th>`,
 * which `text-end` alone cannot move — hence the child selector.
 */
export const END_ALIGNED_COLUMN_META = {
  headerClassName: 'text-end [&>div]:justify-end',
  cellClassName: 'text-end',
} as const
