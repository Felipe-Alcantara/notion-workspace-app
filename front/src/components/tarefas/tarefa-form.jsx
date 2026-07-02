import { useEffect, useState } from 'react'
import { Modal } from '../ui/modal'
import { Input, Select } from '../ui/input'
import { Button } from '../ui/button'

export function TarefaFormModal({ open, onClose, onSubmit, tarefa, opcoes }) {
  const isEdit = !!tarefa
  const [nome, setNome] = useState(tarefa?.nome ?? '')
  const [status, setStatus] = useState(tarefa?.status ?? '')
  const [duracao, setDuracao] = useState(tarefa?.duracao ?? '')
  const [areas, setAreas] = useState(tarefa?.areas ?? [])
  const [prazo, setPrazo] = useState(tarefa?.prazo ?? '')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState(null)

  useEffect(() => {
    if (!open) return
    setNome(tarefa?.nome ?? '')
    setStatus(tarefa?.status ?? '')
    setDuracao(tarefa?.duracao ?? '')
    setAreas(tarefa?.areas ?? [])
    setPrazo(tarefa?.prazo ?? '')
    setErro(null)
    setSalvando(false)
  }, [open, tarefa])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!nome.trim()) {
      setErro('O nome é obrigatório.')
      return
    }
    setSalvando(true)
    setErro(null)
    try {
      const body = { nome: nome.trim() }
      if (status) body.status = status
      if (duracao) body.duracao = duracao
      body.areas = areas
      if (prazo) body.prazo = prazo
      await onSubmit(body)
      onClose()
    } catch (err) {
      setErro(err.message)
    } finally {
      setSalvando(false)
    }
  }

  const toggleArea = (areaId) => {
    setAreas((prev) =>
      prev.includes(areaId) ? prev.filter((a) => a !== areaId) : [...prev, areaId],
    )
  }

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? 'Editar tarefa' : 'Nova tarefa'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="tf-nome" className="block text-xs text-zinc-400 mb-1">
            Tarefa
          </label>
          <Input
            id="tf-nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            placeholder="O que precisa ser feito?"
            autoFocus
          />
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label htmlFor="tf-status" className="block text-xs text-zinc-400 mb-1">
              Etapa
            </label>
            <Select id="tf-status" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Selecionar etapa...</option>
              {opcoes?.status?.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </Select>
          </div>
          <div>
            <label htmlFor="tf-duracao" className="block text-xs text-zinc-400 mb-1">
              Esforço
            </label>
            <Select id="tf-duracao" value={duracao} onChange={(e) => setDuracao(e.target.value)}>
              <option value="">Selecionar esforço...</option>
              {opcoes?.duracao?.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </Select>
          </div>
        </div>

        <div>
          <label htmlFor="tf-prazo" className="block text-xs text-zinc-400 mb-1">
            Prazo
          </label>
          <Input
            id="tf-prazo"
            type="date"
            value={prazo}
            onChange={(e) => setPrazo(e.target.value)}
          />
        </div>

        <div>
          <span className="block text-xs text-zinc-400 mb-2" id="tf-areas-label">
            Áreas da vida
          </span>
          <div className="flex flex-wrap gap-2" aria-labelledby="tf-areas-label">
            {opcoes?.areas?.map((a) => (
              <button
                key={a.id}
                type="button"
                onClick={() => toggleArea(a.id)}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors cursor-pointer ${
                  areas.includes(a.id)
                    ? 'bg-brand-500/20 text-brand-400 border-brand-500/40'
                    : 'bg-zinc-800 text-zinc-400 border-zinc-700/50 hover:text-white'
                }`}
                aria-pressed={areas.includes(a.id)}
              >
                {a.nome}
              </button>
            ))}
            {!opcoes?.areas?.length && (
              <span className="text-xs text-zinc-500">Nenhuma área disponível.</span>
            )}
          </div>
        </div>

        {erro && (
          <p className="text-sm text-red-400" role="alert">{erro}</p>
        )}

        <div className="flex gap-3 justify-end pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancelar</Button>
          <Button type="submit" variant="brand" disabled={salvando}>
            {salvando ? 'Salvando...' : isEdit ? 'Salvar' : 'Criar'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
