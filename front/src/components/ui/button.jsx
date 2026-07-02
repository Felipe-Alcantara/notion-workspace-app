import { cx } from '../../utils/cx'

const variants = {
  default: 'bg-white text-black border-white/10 hover:bg-zinc-100',
  outline: 'bg-transparent text-white border-white/20 hover:bg-white/5',
  ghost: 'bg-transparent text-white border-transparent hover:bg-white/5',
  secondary: 'bg-zinc-800 text-white border-white/10 hover:bg-zinc-700',
  brand: 'bg-brand-500 text-white border-brand-600 hover:bg-brand-600',
}

const sizes = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  icon: 'h-10 w-10 p-2',
}

export function Button({
  variant = 'default',
  size = 'md',
  className,
  children,
  ...props
}) {
  return (
    <button
      className={cx(
        'inline-flex items-center justify-center gap-2 rounded-2xl font-medium',
        'transition-all duration-300 border cursor-pointer',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
