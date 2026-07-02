import { Search, LayoutGrid, List, Columns3 } from 'lucide-react'
import { Input } from '../ui/input'
import { Select } from '../ui/input'
import { Button } from '../ui/button'
import { cx } from '../../utils/cx'

const VIEWS = [
  { id: 'grade', icon: LayoutGrid, label: 'Grade' },
  { id: 'lista', icon: List, label: 'Lista' },
  { id: 'kanban', icon: Columns3, label: 'Kanban' },
]

export function Filtros({
  busca, setBusca,
  statusFiltro, setStatusFiltro,
  duracaoFiltro, setDuracaoFiltro,
  areaFiltro, setAreaFiltro,
  ordenacao, setOrdenacao,
  view, setView,
  opcoes,
  onClear,
}) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none"
          />
          <Input
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar por tarefa, etapa ou área..."
            className="pl-9"
            aria-label="Buscar tarefas"
          />
        </div>

        <div
          className="grid grid-cols-3 overflow-hidden rounded-xl border border-white/10"
          role="radiogroup"
          aria-label="Tipo de visualização"
        >
          {VIEWS.map((v) => (
            <button
              type="button"
              key={v.id}
              onClick={() => setView(v.id)}
              className={cx(
                'flex h-10 min-w-11 items-center justify-center px-3 transition-colors cursor-pointer',
                view === v.id
                  ? 'bg-brand-500/20 text-brand-400'
                  : 'text-zinc-400 hover:text-white hover:bg-white/5',
              )}
              role="radio"
              aria-checked={view === v.id}
              aria-label={v.label}
              title={v.label}
            >
              <v.icon size={16} />
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <Select
          value={statusFiltro}
          onChange={(e) => setStatusFiltro(e.target.value)}
          className="w-auto min-w-[160px]"
          aria-label="Filtrar por etapa"
        >
          <option value="">Todas as etapas</option>
          {opcoes?.status?.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </Select>

        <Select
          value={duracaoFiltro}
          onChange={(e) => setDuracaoFiltro(e.target.value)}
          className="w-auto min-w-[150px]"
          aria-label="Filtrar por esforço"
        >
          <option value="">Qualquer esforço</option>
          {opcoes?.duracao?.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </Select>

        <Select
          value={areaFiltro}
          onChange={(e) => setAreaFiltro(e.target.value)}
          className="w-auto min-w-[140px]"
          aria-label="Filtrar por área da vida"
        >
          <option value="">Todas as áreas</option>
          {opcoes?.areas?.map((a) => (
            <option key={a.id} value={a.id}>{a.nome}</option>
          ))}
        </Select>

        <Select
          value={ordenacao}
          onChange={(e) => setOrdenacao(e.target.value)}
          className="w-auto min-w-[140px]"
          aria-label="Ordenar por"
        >
          <option value="nome">Tarefa A-Z</option>
          <option value="nome-desc">Tarefa Z-A</option>
          <option value="prazo">Prazo (mais perto)</option>
          <option value="status">Etapa</option>
        </Select>

        <Button type="button" variant="ghost" onClick={onClear}>
          Limpar
        </Button>
      </div>
    </div>
  )
}
