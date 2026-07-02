# Front React

SPA do Ciclo 2 para operar tarefas do Notion pelo contrato REST em `docs/CONTRATOS.md`.

## Rodar localmente

```bash
cd front
npm install
npm run dev
```

O Vite exige Node 20.19+ ou 22.12+. Ele sobe em `http://localhost:5173` e proxia
`/api` para `http://127.0.0.1:8000`.

O app usa o Notion como fonte de verdade por meio da API Django. Se a API falhar,
o front mostra erro; mock só roda quando você ativar explicitamente:

```bash
VITE_MOCK_API=true npm run dev
```

## Qualidade

```bash
npm run lint
npm run build
```

O gate completo do repositório roda a partir da raiz:

```bash
python3 scripts/quality_check.py
```

## Funcionalidades

- Duas abas: **Tarefas** (a todolist, com escrita) e **Explorar** (read-only).
- **Explorar** lista os databases visíveis à integração e mostra qualquer um
  numa tabela genérica que se adapta ao schema — não só a todolist. Usa
  `GET /api/databases` e `GET /api/databases/{id}`. Só leitura por enquanto.
- Visualizações em grade, lista e kanban.
- Indicação explícita da **database ativa** e da **data source** do Notion, com link
  para abrir a tabela atual e conferir se a interface está apontando para a fonte certa.
- Busca, filtros persistentes por etapa/esforço/área e ordenação. Os valores
  de etapa/esforço/área vêm do Notion e são enviados de volta sem tradução
  local.
- **Clicar numa tarefa abre a página dela no Notion** (a nota, em nova aba), usando
  a `url` do contrato. A edição fica no **botão de lápis** de cada tarefa.
- Modal de criação/edição usando `POST /api/tarefas`, `PATCH /api/tarefas/{id}` e
  `GET /api/opcoes`.
- Estados de carregamento, vazio e erro com feedback acessível.
