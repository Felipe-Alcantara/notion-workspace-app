import { cx } from '../../utils/cx'

export function Card({ className, children, ...props }) {
  return (
    <div
      className={cx(
        'rounded-2xl border border-white/10 bg-zinc-950/50',
        'transition-all duration-300 hover:border-white/20',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ className, children }) {
  return (
    <div className={cx('p-5 border-b border-white/5', className)}>
      {children}
    </div>
  )
}

export function CardContent({ className, children }) {
  return <div className={cx('p-5', className)}>{children}</div>
}

export function CardFooter({ className, children }) {
  return (
    <div
      className={cx(
        'p-5 border-t border-white/5 flex items-center gap-3',
        className,
      )}
    >
      {children}
    </div>
  )
}
