# AGENTS.md — notion-workspace-app

Aplicação completa (Django + React + MCP + TUI), módulo do ecossistema [Automações do Notion](https://github.com/Felipe-Alcantara/Automa-es-do-Notion) — o hub tem o roteamento completo entre módulos.

## Arquitetura (fronteiras sagradas)

```
start_app.py            → launcher TUI (instala deps, sobe Django + Vite, abre navegador)
server/config/          → projeto Django
server/core/config.py   → configuração por ambiente (imutável, nunca vaza segredo)
server/integrations/    → Notion local + shims para adaptadores GitHub/OpenRouter do notion-starter
server/services/        → shims para notion_starter.services (casos de uso compartilhados)
server/api/             → borda REST — views finas, sem regra de negócio
server/mcp_server.py    → borda MCP — ferramentas notion.*, fina sobre services
server/operations/      → estado operacional em SQLite (Job/Lock); conteúdo mora no Notion
front/src/              → SPA React (Vite): kanban, filtros, exploração do workspace
```

- `api` e `mcp_server` não têm regra de negócio; `services` não conhece HTTP de borda.
- A base Notion vem da lib [notion-starter](https://github.com/Felipe-Alcantara/notion-starter) (via `requirements.txt`).

## Camada compartilhada

`server/integrations/github.py`, `server/integrations/openrouter.py` e `server/services/*` comuns
são shims para `notion-starter`. Bugfix de regra compartilhada deve ser feito em
`modules/notion-starter/src/notion_starter/`; a borda REST/MCP/Django continua neste repo.

## Testar

```bash
python -m pytest        # front: cd front && npm test / npx oxlint
```

Falhas pré-existentes conhecidas no Windows: 2 em `test_start_app`, 1 em `test_services_ingestao` — não são regressão sua.

## Convenções

Código e mensagens em português; Conventional Commits; nunca commitar `.env` ou SQLite.
