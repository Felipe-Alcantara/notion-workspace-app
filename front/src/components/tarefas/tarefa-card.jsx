import { Card, CardContent } from '../ui/card'
import { StatusBadge, Badge } from '../ui/badge'
import { Button } from '../ui/button'
import { Calendar, Clock, Layers, Pencil, ExternalLink } from 'lucide-react'
import { abrirNoNotion } from '../../utils/abrir-no-notion'

export function TarefaCard({ tarefa, onEdit }) {
  const temUrl = Boolean(tarefa.url)
  return (
    <Card
      className={temUrl ? 'cursor-pointer hover:border-brand-500/30' : ''}
      onClick={temUrl ? () => abrirNoNotion(tarefa) : undefined}
      role={temUrl ? 'button' : undefined}
      tabIndex={temUrl ? 0 : undefined}
      aria-label={temUrl ? `Abrir no Notion: ${tarefa.nome}` : undefined}
      onKeyDown={temUrl ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); abrirNoNotion(tarefa) }
      } : undefined}
    >
      <CardContent className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-sm font-semibold text-white leading-tight">
            {tarefa.nome}
            {temUrl && <ExternalLink size={12} className="inline ml-1.5 text-zinc-500" aria-hidden="true" />}
          </h3>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 shrink-0 text-zinc-400 hover:text-white"
            aria-label={`Editar tarefa: ${tarefa.nome}`}
            onClick={(e) => { e.stopPropagation(); onEdit(tarefa) }}
          >
            <Pencil size={14} />
          </Button>
        </div>

        <div className="flex flex-wrap gap-2">
          <StatusBadge status={tarefa.status} />
          {tarefa.duracao && (
            <Badge className="bg-zinc-800 text-zinc-300 border-zinc-700/50">
              <Clock size={12} className="mr-1" />
              {tarefa.duracao}
            </Badge>
          )}
        </div>

        {tarefa.areas_nomes?.length > 0 && (
          <div className="flex items-center gap-1 text-xs text-zinc-400">
            <Layers size={12} />
            {tarefa.areas_nomes.join(', ')}
          </div>
        )}

        {tarefa.prazo && (
          <div className="flex items-center gap-1 text-xs text-zinc-500">
            <Calendar size={12} />
            {new Date(tarefa.prazo).toLocaleDateString('pt-BR')}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
