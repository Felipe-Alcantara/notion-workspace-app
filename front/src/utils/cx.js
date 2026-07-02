/** Combina classes condicionalmente, removendo valores falsy. */
export function cx(...classes) {
  return classes.filter(Boolean).join(' ')
}
