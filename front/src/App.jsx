import { useState } from 'react'
import { Compass, ListTodo } from 'lucide-react'
import { Navbar } from './components/layout/navbar'
import { PainelTarefas } from './components/tarefas/painel-tarefas'
import { ViewExplorar } from './components/explorar/view-explorar'

const ABAS = [
  { id: 'tarefas', rotulo: 'Tarefas', icone: ListTodo },
  { id: 'explorar', rotulo: 'Explorar', icone: Compass },
]

function App() {
  const [aba, setAba] = useState('tarefas')

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      <Navbar />

      <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:py-8">
        <nav className="flex gap-1 rounded-2xl border border-white/10 bg-zinc-900/40 p-1" aria-label="Seções">
          {ABAS.map(({ id, rotulo, icone: Icone }) => (
            <button
              key={id}
              type="button"
              onClick={() => setAba(id)}
              aria-current={aba === id ? 'page' : undefined}
              className={[
                'flex flex-1 items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-colors',
                aba === id ? 'bg-brand-500 text-white' : 'text-zinc-300 hover:bg-white/5',
              ].join(' ')}
            >
              <Icone size={16} aria-hidden="true" />
              {rotulo}
            </button>
          ))}
        </nav>

        {aba === 'tarefas' ? <PainelTarefas /> : <ViewExplorar />}
      </main>
    </div>
  )
}

export default App
