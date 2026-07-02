import { TarefaCard } from './tarefa-card'

export function ViewGrade({ tarefas, onEdit }) {
  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {tarefas.map((t) => (
        <TarefaCard key={t.id} tarefa={t} onEdit={onEdit} />
      ))}
    </div>
  )
}
