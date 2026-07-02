import { useEffect, useState } from 'react'
import { api } from '../api/client'

export function useDatabaseAtual() {
  const [database, setDatabase] = useState(null)
  const [erro, setErro] = useState(null)

  useEffect(() => {
    let cancelado = false
    api.databaseAtual()
      .then((data) => {
        if (!cancelado) setDatabase(data)
      })
      .catch((e) => {
        if (!cancelado) setErro(e.message)
      })
    return () => {
      cancelado = true
    }
  }, [])

  return { database, erro }
}
