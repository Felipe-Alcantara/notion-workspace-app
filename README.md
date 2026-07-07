# notion-workspace-app

Aplicação local completa para operar o Notion: **API Django + SPA React + servidor MCP + launcher TUI**. Gerencie tarefas em kanban/grade/lista, explore o workspace, sincronize repositórios do GitHub com databases do Notion e exponha tudo isso para IAs via MCP.

> Parte do ecossistema [Automações do Notion](https://github.com/Felipe-Alcantara/Automa-es-do-Notion). Construído sobre a biblioteca [notion-starter](https://github.com/Felipe-Alcantara/notion-starter).

## Componentes

| Camada | Pasta | Descrição |
| --- | --- | --- |
| Launcher | `start_app.py` | TUI que instala dependências, sobe servidor e front com um comando |
| API | `server/api` | REST em Django para tarefas, exploração e opções |
| Services | `server/services` | Shims para `notion_starter.services`: tarefas, clonagem, ingestão, IA, sincronização GitHub |
| Integrações | `server/integrations` | Notion local + shims para GitHub e OpenRouter |
| MCP | `server/mcp_server.py` | Servidor MCP expondo as operações para clientes de IA |
| Front | `front/` | SPA React (Vite) com kanban, filtros e exploração do workspace |

## Início rápido

```bash
git clone https://github.com/Felipe-Alcantara/notion-workspace-app.git
cd notion-workspace-app
pip install -r requirements.txt
cp .env.example .env   # preencha NOTION_TOKEN e NOTION_DATABASE_ID
python start_app.py
```

O launcher cuida do resto: sobe o Django, o Vite e abre o navegador.

## Testes

```bash
pytest
```

## Licença

MIT
