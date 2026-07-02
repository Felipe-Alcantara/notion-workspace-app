/**
 * API client para o backend Django (CONTRATOS.md §2).
 *
 * Em uso normal, toda leitura/escrita passa pela API Django, que usa o Notion
 * como fonte de verdade. O mock só é usado quando VITE_MOCK_API=true.
 */

const USE_MOCK = import.meta.env.VITE_MOCK_API === 'true'

// ─── Mock data (contrato §1) ────────────────────────────────────────────

const MOCK_OPCOES = {
  status: [
    'Entrada',
    'Urgente',
    'Assim que possível',
    'Delegar',
    'Aguardando resposta',
    'Referência',
    'Concluída',
    'Algum dia',
    'Agendada',
  ],
  duracao: ['Agora', 'Hoje', 'Minutos', 'Poucas horas', 'Muitas horas', 'Dias', 'Concluída'],
  areas: [
    { id: 'area-1', nome: 'Estudos' },
    { id: 'area-2', nome: 'Trabalho' },
    { id: 'area-3', nome: 'Saúde' },
    { id: 'area-4', nome: 'Projetos' },
  ],
}

let mockIdCounter = 7

const MOCK_TAREFAS = [
  {
    id: 'mock-1',
    nome: 'Estudar a API do Notion',
    status: 'Entrada',
    prazo: '2026-07-01',
    duracao: 'Dias',
    areas: ['area-1'],
    areas_nomes: ['Estudos'],
    url: null,
  },
  {
    id: 'mock-2',
    nome: 'Configurar CI/CD do repositório',
    status: 'Entrada',
    prazo: null,
    duracao: 'Poucas horas',
    areas: ['area-4'],
    areas_nomes: ['Projetos'],
    url: null,
  },
  {
    id: 'mock-3',
    nome: 'Revisar PR do front React',
    status: 'Assim que possível',
    prazo: '2026-06-28',
    duracao: 'Minutos',
    areas: ['area-2'],
    areas_nomes: ['Trabalho'],
    url: null,
  },
  {
    id: 'mock-4',
    nome: 'Treino de força',
    status: 'Urgente',
    prazo: null,
    duracao: 'Poucas horas',
    areas: ['area-3'],
    areas_nomes: ['Saúde'],
    url: null,
  },
  {
    id: 'mock-5',
    nome: 'Escrever documentação da CLI',
    status: 'Aguardando resposta',
    prazo: '2026-07-10',
    duracao: 'Dias',
    areas: ['area-4', 'area-1'],
    areas_nomes: ['Projetos', 'Estudos'],
    url: null,
  },
  {
    id: 'mock-6',
    nome: 'Organizar notas do semestre',
    status: 'Concluída',
    prazo: '2026-06-20',
    duracao: 'Dias',
    areas: ['area-1'],
    areas_nomes: ['Estudos'],
    url: null,
  },
]

// ─── Helpers ─────────────────────────────────────────────────────────────

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(path, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    })
  } catch (error) {
    const apiError = new Error('Backend indisponivel.')
    apiError.cause = error
    throw apiError
  }
  const data = await res.json()
  if (!res.ok) {
    const msg = data?.erro?.mensagem ?? `Erro ${res.status}`
    const error = new Error(msg)
    error.status = res.status
    throw error
  }
  return data
}

// ─── Mock implementations ────────────────────────────────────────────────

const mockApi = {
  async listarTarefas(filtros = {}) {
    await delay(300)
    let list = [...MOCK_TAREFAS]
    if (filtros.status) list = list.filter((t) => t.status === filtros.status)
    if (filtros.duracao) list = list.filter((t) => t.duracao === filtros.duracao)
    if (filtros.area) list = list.filter((t) => (t.areas ?? []).includes(filtros.area))
    return { tarefas: list }
  },

  async criarTarefa(body) {
    await delay(400)
    const tarefa = {
      id: `mock-${++mockIdCounter}`,
      nome: body.nome,
      status: body.status ?? 'Entrada',
      prazo: body.prazo ?? null,
      duracao: body.duracao ?? null,
      areas: body.areas ?? [],
      areas_nomes: (body.areas ?? []).map(
        (id) => MOCK_OPCOES.areas.find((a) => a.id === id)?.nome ?? id,
      ),
      url: null,
    }
    MOCK_TAREFAS.push(tarefa)
    return tarefa
  },

  async editarTarefa(id, body) {
    await delay(300)
    const idx = MOCK_TAREFAS.findIndex((t) => t.id === id)
    if (idx === -1) throw new Error('Tarefa nao encontrada')
    const tarefa = { ...MOCK_TAREFAS[idx], ...body }
    if (body.areas) {
      tarefa.areas_nomes = body.areas.map(
        (aid) => MOCK_OPCOES.areas.find((a) => a.id === aid)?.nome ?? aid,
      )
    }
    MOCK_TAREFAS[idx] = tarefa
    return tarefa
  },

  async opcoes() {
    await delay(200)
    return MOCK_OPCOES
  },
}

function delay(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

// ─── Real API ────────────────────────────────────────────────────────────

const realApi = {
  async listarTarefas(filtros = {}) {
    const qs = new URLSearchParams()
    if (filtros.status) qs.set('status', filtros.status)
    if (filtros.duracao) qs.set('duracao', filtros.duracao)
    if (filtros.area) qs.set('area', filtros.area)
    const query = qs.toString()
    return request(`/api/tarefas${query ? `?${query}` : ''}`)
  },

  async criarTarefa(body) {
    return request('/api/tarefas', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  async editarTarefa(id, body) {
    return request(`/api/tarefas/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    })
  },

  async opcoes() {
    return request('/api/opcoes')
  },

  async databaseAtual() {
    return request('/api/database-atual')
  },

  async listarDatabases(query = '') {
    const qs = query ? `?query=${encodeURIComponent(query)}` : ''
    return request(`/api/databases${qs}`)
  },

  async descreverDatabase(id) {
    return request(`/api/databases/${encodeURIComponent(id)}`)
  },
}

// ─── Mock de exploração (read-only) ───────────────────────────────────────

const MOCK_DATABASES = [
  { id: 'db-tarefas', titulo: 'Tarefas — HOME', url: null },
  { id: 'db-livros', titulo: 'Livros', url: null },
]

const MOCK_DESCRICAO = {
  'db-tarefas': {
    id: 'db-tarefas',
    colunas: [
      { nome: 'Tarefa', tipo: 'title' },
      { nome: 'Etapa', tipo: 'status' },
      { nome: 'Esforço', tipo: 'status' },
    ],
    linhas: MOCK_TAREFAS.map((t) => ({
      id: t.id,
      url: t.url,
      valores: { Tarefa: t.nome, Etapa: t.status, Esforço: t.duracao ?? '' },
    })),
  },
  'db-livros': {
    id: 'db-livros',
    colunas: [
      { nome: 'Título', tipo: 'title' },
      { nome: 'Autor', tipo: 'rich_text' },
      { nome: 'Lido', tipo: 'checkbox' },
    ],
    linhas: [
      { id: 'l1', url: null, valores: { Título: 'O Hobbit', Autor: 'Tolkien', Lido: '✓' } },
      { id: 'l2', url: null, valores: { Título: 'Duna', Autor: 'Herbert', Lido: '' } },
    ],
  },
}

const mockExploracao = {
  async listarDatabases(query = '') {
    await delay(200)
    const q = query.trim().toLowerCase()
    const itens = q
      ? MOCK_DATABASES.filter((d) => d.titulo.toLowerCase().includes(q))
      : MOCK_DATABASES
    return { databases: itens }
  },
  async descreverDatabase(id) {
    await delay(250)
    return MOCK_DESCRICAO[id] ?? { id, colunas: [], linhas: [] }
  },
}

// ─── Exported API (mock explícito) ────────────────────────────────────────

function escolherApi(fn, mockFn) {
  return USE_MOCK ? mockFn : fn
}

export const api = {
  listarTarefas: escolherApi(realApi.listarTarefas, mockApi.listarTarefas),
  criarTarefa: escolherApi(realApi.criarTarefa, mockApi.criarTarefa),
  editarTarefa: escolherApi(realApi.editarTarefa, mockApi.editarTarefa),
  opcoes: escolherApi(realApi.opcoes, mockApi.opcoes),
  databaseAtual: escolherApi(
    realApi.databaseAtual,
    async () => ({ id: 'db-tarefas', titulo: 'Tarefas — HOME', url: null }),
  ),
  listarDatabases: escolherApi(realApi.listarDatabases, mockExploracao.listarDatabases),
  descreverDatabase: escolherApi(realApi.descreverDatabase, mockExploracao.descreverDatabase),
}
