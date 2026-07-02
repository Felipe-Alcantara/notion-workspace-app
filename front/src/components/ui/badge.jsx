import { cx } from '../../utils/cx'
import { statusColor } from '../../utils/status-color'

export function Badge({ className, children, ...props }) {
  return (
    <span
      className={cx(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-medium border',
        className,
      )}
      {...props}
    >
      {children}
    </span>
  )
}

export function StatusBadge({ status }) {
  return (
    <Badge className={statusColor(status)}>
      {status ?? 'Sem etapa'}
    </Badge>
  )
}
