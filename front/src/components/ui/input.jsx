import { forwardRef } from 'react'
import { cx } from '../../utils/cx'

export const Input = forwardRef(function Input({ className, ...props }, ref) {
  return (
    <input
      ref={ref}
      className={cx(
        'w-full h-10 rounded-xl bg-zinc-800/50 border border-white/10 px-3',
        'text-sm text-white placeholder:text-zinc-400 outline-none',
        'focus:border-brand-500/60 focus:ring-2 focus:ring-brand-500/20',
        'transition-all duration-200',
        className,
      )}
      {...props}
    />
  )
})

export function Select({ className, children, ...props }) {
  return (
    <select
      className={cx(
        'w-full h-10 rounded-xl bg-zinc-800/50 border border-white/10 px-3',
        'text-sm text-white outline-none appearance-none',
        'focus:border-brand-500/60 focus:ring-2 focus:ring-brand-500/20',
        'transition-all duration-200',
        className,
      )}
      {...props}
    >
      {children}
    </select>
  )
}
