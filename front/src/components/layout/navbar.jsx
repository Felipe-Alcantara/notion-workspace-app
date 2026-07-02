import { Layers } from 'lucide-react'

export function Navbar() {
  return (
    <nav className="sticky top-0 z-40 border-b border-white/5 bg-zinc-950/90 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center gap-3">
        <Layers size={20} className="text-brand-400" />
        <span className="text-sm font-semibold text-white">Tarefas</span>
        <span className="text-xs text-zinc-500">Notion</span>
      </div>
    </nav>
  )
}
