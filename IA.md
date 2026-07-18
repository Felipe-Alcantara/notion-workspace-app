# 🤖 IA.md — Contexto operacional do notion-workspace-app

> **O que é**: Memória técnica deste repositório para retomada de contexto por IA ou
> por um novo mantenedor, sem reler todo o código. Baseado no template de contexto do
> Felixo System Design.
>
> **Histórico anterior**: este módulo nasceu da separação do monorepo
> [Automações do Notion](https://github.com/Felipe-Alcantara/Automa-es-do-Notion)
> em 2026-07-02. A linha do tempo anterior (fases do servidor, front, MCP e launcher)
> permanece no `IA.md` do hub — este arquivo cobre a vida do módulo a partir da
> separação.

---

## 📊 ESTADO ATUAL (RESUMO VIVO)

Última atualização: [2026-07-18]

- Fase: produto local funcional com launcher, API Django, SPA React e servidor
  MCP sobre o `notion-starter`.
- Qualidade: 256 testes verdes, 2 skips esperados, `ruff` e `oxlint` limpos e
  build Vite aprovado; CI cobre Python 3.10–3.13 e o frontend em Node 22.
- Documentação: README alinhado ao Felixo System Design e contrato de qualidade
  centralizado em `QUALIDADE.md`.
- Próximos passos abertos: escrita genérica na exploração, novas visualizações e
  empacotamento do launcher.
- Risco conhecido: dependências Python usam limites mínimos e são monitoradas
  pela matriz de CI; o frontend possui lockfile.

---

## 🎯 OBJETIVO DO PROJETO

[2026-07-02] `notion-workspace-app` é a aplicação completa do ecossistema: API REST
Django (`server/`), SPA React com grade/lista/kanban e aba Explorar (`front/`),
servidor MCP com as ferramentas `notion.*` (`server/mcp_server.py`) e o launcher TUI
`start_app.py` ("Iniciar tudo": migrações, API, front e navegador).

---

## 📐 DECISÕES DE ARQUITETURA

- [2026-07-02] Camadas herdadas do monorepo (registradas no hub): `config/`,
  `core/`, `integrations/`, `services/`, `api/`, `operations/`. Fronteira sagrada:
  `api` não tem regra de negócio; `services` não conhece HTTP; só o `NotionClient`
  fala com a API do Notion. A borda MCP é processo independente e fino sobre os
  services.
- [2026-07-02] A regra de negócio compartilhada foi consolidada no
  `notion-starter`; `integrations/github.py`, `integrations/openrouter.py` e os
  `services/` comuns aqui são shims de compatibilidade.
- [2026-07-08] Decisão: Django e React continuam no mesmo repositório de propósito —
  formam um único produto (app local com launcher); a proposta original de separar
  frontend e backend em repositórios distintos foi considerada e descartada.

---

## 🛠️ STACK & DEPENDÊNCIAS

- Python 3.10+; `requirements.txt`: `notion-starter` (git), `django>=5.0`,
  `questionary`/`rich` (TUI), `mcp>=1.28,<2`, e dev `pytest`/`responses`/`ruff`.
- Front: Vite + React 18 + Tailwind; lint com `oxlint`; Node 22+.

---

## 🧪 TESTES & GATE

- Gate Python: `ruff check .` + `python -m pytest` (272 testes em 2026-07-08, sem rede).
- Gate front: `npm run lint` + `npm run build` em `front/`.
- CI: GitHub Actions (`.github/workflows/ci.yml`) com jobs Python (3.10–3.13) e front.

---

## 🐛 BUGS & FIXES RELEVANTES

- [2026-07-08] FIX (portabilidade Windows): 3 testes falhavam só no Windows e eram
  tidos como "pré-existentes conhecidos". Causas: (1) `test_services_ingestao`
  escrevia arquivo com a codificação padrão da plataforma enquanto a produção lê
  UTF-8 — o teste passou a escrever com `encoding="utf-8"`; (2–3) `test_start_app`
  comparava caminhos POSIX literais com a saída de `Path`/`Path.absolute()`, que no
  Windows usa `\` — os testes passaram a aplicar a mesma normalização da produção.
  Nenhuma mudança de comportamento em produção.

---

## 🧠 LINHA DO TEMPO

- [2026-07-02] ✅ Módulo extraído do monorepo (server + front + MCP + start_app).
- [2026-07-08] ✅ Alinhamento ao padrão de qualidade Felixo: `ruff check .` zerado
  (12 imports reordenados pós-consolidação + 1 linha longa), 3 testes
  Windows-only corrigidos (suíte 100% verde em Windows e POSIX), adicionados
  `CONTRIBUTING.md`, `IA.md` e CI GitHub Actions. Validação: 272 testes verdes,
  ruff limpo, `npm run lint` e `npm run build` verdes.
- [2026-07-13] ✅ Cinco ferramentas MCP novas, paridade com a CLI:
  `notion.create_database`, `notion.import_spreadsheet`, `notion.upload_file`,
  `notion.move_page` e `notion.move_database` — bordas finas sobre o
  notion-starter. Decisão: paridade só no MCP; a API REST segue servindo apenas
  o front. Validação: 255 testes verdes (2 skips) e ruff limpo.
- [2026-07-18] ✅ Documentação alinhada ao Felixo System Design: README passou a
  ter badges, índice, árvore real, guia de uso e rodapé open source;
  `QUALIDADE.md` centralizou os gates Python/frontend e registrou a exceção
  motivada de versões mínimas no backend. Motivo: deixar setup e critério de
  pronto verificáveis sem alterar contratos ou dependências. Validação pelo
  orquestrador: 256 testes verdes, 2 skips esperados, `ruff`/`oxlint` limpos e
  build Vite aprovado; mudanças desta rodada restritas à documentação.

---

Ideias abertas à contribuição: escrita genérica na aba Explorar, mais
visualizações no kanban, empacotamento do launcher para distribuição.
