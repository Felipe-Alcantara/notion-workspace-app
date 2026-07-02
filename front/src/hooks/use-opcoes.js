import { useState, useEffect } from 'react'
import { api } from '../api/client'

export function useOpcoes() {
  const [opcoes, setOpcoes] = useState(null)
  const [erro, setErro] = useState(null)

  useEffect(() => {
    let cancelled = false
    api.opcoes()
      .then((data) => { if (!cancelled) setOpcoes(data) })
      .catch((e) => { if (!cancelled) setErro(e.message) })
    return () => { cancelled = true }
  }, [])

  return { opcoes, erro }
}
