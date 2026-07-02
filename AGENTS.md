# AGENTS.md — notion-workspace-app

Aplicação completa (Django + React + MCP + TUI), módulo do ecossistema [Automações do Notion](https://github.com/Felipe-Alcantara/Automa-es-do-Notion) — o hub tem o roteamento completo entre módulos.

## Arquitetura (fronteiras sagradas)

```
start_app.py            → launcher TUI (instala deps, sobe Django + Vite, abre navegador)
server/config/          → projeto Django
server/core/config.py   → configuração por ambiente (imutável, nunca vaza segredo)
server/integrations/    → adaptadores (Notion via notion-starter, GitHub, OpenRouter)
server/services/        → regra de negócio (casos de uso)
server/api/             → borda REST — views finas, sem regra de negócio
server/mcp_server.py    → borda MCP — ferramentas notion.*, fina sobre services
server/operations/      → estado operacional em SQLite (Job/Lock); conteúdo mora no Notion
front/src/              → SPA React (Vite): kanban, filtros, exploração do workspace
```

- `api` e `mcp_server` não têm regra de negócio; `services` não conhece HTTP de borda.
- A base Notion vem da lib [notion-starter](https://github.com/Felipe-Alcantara/notion-starter) (via `requirements.txt`).

## ⚠️ Camada duplicada

`server/core/`, `server/integrations/` e `server/services/` também existem (como pacotes de topo) em `notion-tasks-cli`. Bugfix nessa camada deve ser aplicado **nos dois repositórios**. (Roadmap: consolidar no `notion-starter`.)

## Testar

```bash
python -m pytest        # front: cd front && npm test / npx oxlint
```

Falhas pré-existentes conhecidas no Windows: 2 em `test_start_app`, 1 em `test_services_ingestao` — não são regressão sua.

## Convenções

Código e mensagens em português; Conventional Commits; nunca commitar `.env` ou SQLite.
