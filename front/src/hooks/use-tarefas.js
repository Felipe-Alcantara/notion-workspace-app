import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'

export function useTarefas(filtros = {}) {
  const [tarefas, setTarefas] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)
  const { status = '', duracao = '', area = '' } = filtros

  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro(null)
    try {
      const data = await api.listarTarefas({ status, duracao, area })
      setTarefas(data.tarefas)
    } catch (e) {
      setErro(e.message)
    } finally {
      setCarregando(false)
    }
  }, [status, duracao, area])

  useEffect(() => { carregar() }, [carregar])

  const criar = useCallback(async (body) => {
    const tarefa = await api.criarTarefa(body)
    await carregar()
    return tarefa
  }, [carregar])

  const editar = useCallback(async (id, body) => {
    const tarefa = await api.editarTarefa(id, body)
    await carregar()
    return tarefa
  }, [carregar])

  return { tarefas, carregando, erro, carregar, criar, editar }
}
