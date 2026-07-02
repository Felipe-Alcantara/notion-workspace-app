import { TarefaCard } from './tarefa-card'
import { statusDotColor } from '../../utils/status-color'

export function ViewKanban({ tarefas, statusList, onEdit }) {
  const colunas = statusList.map((s) => ({
    status: s,
    itens: tarefas.filter((t) => t.status === s),
  }))

  // Inclui tarefas sem status correspondente
  const statusSet = new Set(statusList)
  const semStatus = tarefas.filter((t) => !statusSet.has(t.status))
  if (semStatus.length > 0) {
    colunas.unshift({ status: null, itens: semStatus })
  }

  return (
    <div className="flex gap-4 overflow-x-auto pb-4" role="region" aria-label="Quadro por etapa">
      {colunas.map((col) => (
        <div
          key={col.status ?? '__sem_status'}
          className="min-w-[280px] max-w-[320px] flex-shrink-0"
        >
          <div className="flex items-center gap-2 mb-3 px-1">
            <span
              className={`inline-block w-2 h-2 rounded-full ${statusDotColor(col.status)}`}
            />
            <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
              {col.status ?? 'Sem etapa'}
            </h3>
            <span className="text-xs text-zinc-500">{col.itens.length}</span>
          </div>

          <div className="space-y-3">
            {col.itens.map((t) => (
              <TarefaCard key={t.id} tarefa={t} onEdit={onEdit} />
            ))}
            {col.itens.length === 0 && (
              <div className="rounded-2xl border border-dashed border-white/10 p-6 text-center text-xs text-zinc-500">
                Nenhuma tarefa
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
