import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'

/**
 * Estado da aba "Explorar": lista de databases visíveis e a descrição
 * (colunas + linhas) do database selecionado. Read-only.
 */
export function useExploracao() {
  const [databases, setDatabases] = useState([])
  const [carregandoLista, setCarregandoLista] = useState(true)
  const [erroLista, setErroLista] = useState(null)

  const [selecionado, setSelecionado] = useState(null)
  const [descricao, setDescricao] = useState(null)
  const [carregandoDescricao, setCarregandoDescricao] = useState(false)
  const [erroDescricao, setErroDescricao] = useState(null)

  const carregarLista = useCallback(async () => {
    setCarregandoLista(true)
    setErroLista(null)
    try {
      const data = await api.listarDatabases()
      setDatabases(data.databases ?? [])
    } catch (e) {
      setErroLista(e.message)
    } finally {
      setCarregandoLista(false)
    }
  }, [])

  useEffect(() => {
    carregarLista()
  }, [carregarLista])

  const selecionar = useCallback(async (database) => {
    setSelecionado(database)
    setDescricao(null)
    setCarregandoDescricao(true)
    setErroDescricao(null)
    try {
      const data = await api.descreverDatabase(database.id)
      setDescricao(data)
    } catch (e) {
      setErroDescricao(e.message)
    } finally {
      setCarregandoDescricao(false)
    }
  }, [])

  return {
    databases,
    carregandoLista,
    erroLista,
    selecionado,
    descricao,
    carregandoDescricao,
    erroDescricao,
    selecionar,
    recarregarLista: carregarLista,
  }
}
