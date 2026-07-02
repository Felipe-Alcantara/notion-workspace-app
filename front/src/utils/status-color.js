const STATUS_COLORS = {
  Entrada: 'bg-zinc-500/10 text-zinc-300 border-zinc-500/20',
  '00. Inbox': 'bg-zinc-500/10 text-zinc-300 border-zinc-500/20',
  '01. Urgente': 'bg-red-500/10 text-red-300 border-red-500/20',
  Urgente: 'bg-red-500/10 text-red-300 border-red-500/20',
  '01. Priorizadas': 'bg-yellow-500/10 text-yellow-300 border-yellow-500/20',
  '02. ASAP': 'bg-red-500/10 text-red-300 border-red-500/20',
  'Assim que possível': 'bg-red-500/10 text-red-300 border-red-500/20',
  '03. Delegar': 'bg-blue-500/10 text-blue-300 border-blue-500/20',
  Delegar: 'bg-blue-500/10 text-blue-300 border-blue-500/20',
  '03. Fazendo': 'bg-blue-500/10 text-blue-300 border-blue-500/20',
  '04. Aguardando Resposta': 'bg-orange-500/10 text-orange-300 border-orange-500/20',
  'Aguardando resposta': 'bg-orange-500/10 text-orange-300 border-orange-500/20',
  '04. Esperando': 'bg-orange-500/10 text-orange-300 border-orange-500/20',
  '05. Referências': 'bg-purple-500/10 text-purple-300 border-purple-500/20',
  Referência: 'bg-purple-500/10 text-purple-300 border-purple-500/20',
  '05. Adiadas': 'bg-purple-500/10 text-purple-300 border-purple-500/20',
  '06. Feito': 'bg-green-500/10 text-green-300 border-green-500/20',
  Concluída: 'bg-green-500/10 text-green-300 border-green-500/20',
  '07. Someday': 'bg-sky-500/10 text-sky-300 border-sky-500/20',
  'Algum dia': 'bg-sky-500/10 text-sky-300 border-sky-500/20',
  'xx. Agendado': 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20',
  Agendada: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20',
}

const STATUS_DOTS = {
  Entrada: 'bg-zinc-400',
  '00. Inbox': 'bg-zinc-400',
  '01. Urgente': 'bg-red-400',
  Urgente: 'bg-red-400',
  '01. Priorizadas': 'bg-yellow-400',
  '02. ASAP': 'bg-red-400',
  'Assim que possível': 'bg-red-400',
  '03. Delegar': 'bg-blue-400',
  Delegar: 'bg-blue-400',
  '03. Fazendo': 'bg-blue-400',
  '04. Aguardando Resposta': 'bg-orange-400',
  'Aguardando resposta': 'bg-orange-400',
  '04. Esperando': 'bg-orange-400',
  '05. Referências': 'bg-purple-400',
  Referência: 'bg-purple-400',
  '05. Adiadas': 'bg-purple-400',
  '06. Feito': 'bg-green-400',
  Concluída: 'bg-green-400',
  '07. Someday': 'bg-sky-400',
  'Algum dia': 'bg-sky-400',
  'xx. Agendado': 'bg-indigo-400',
  Agendada: 'bg-indigo-400',
}

export function statusColor(status) {
  if (!status) return 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
  return (
    STATUS_COLORS[status] ??
    'bg-brand-500/10 text-brand-400 border-brand-500/20'
  )
}

export function statusDotColor(status) {
  if (!status) return 'bg-zinc-500'
  return STATUS_DOTS[status] ?? 'bg-brand-400'
}
