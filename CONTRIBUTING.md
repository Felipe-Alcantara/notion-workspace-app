# 🤝 Contribuindo com o notion-workspace-app

Obrigado por querer contribuir! Este repositório é a aplicação completa do
ecossistema [Automações do Notion](https://github.com/Felipe-Alcantara/Automa-es-do-Notion):
API Django, SPA React, servidor MCP e o launcher `start_app.py`. Issues, correções
de documentação, melhorias de UX no front, novos endpoints e testes são bem-vindos.

> Contribuições devem preservar os contratos existentes (API REST, ferramentas
> MCP), a documentação viva e o gate de qualidade abaixo.

---

## 🚀 Como Contribuir

1. **Faça um fork** do repositório.
2. **Crie uma branch** descritiva (`fix/...`, `feat/...`, `docs/...`) para mudanças
   grandes; correções pequenas podem ir direto no `main` de quem mantém.
3. **Faça suas mudanças** seguindo os padrões abaixo.
4. **Rode os testes e o lint** antes de abrir o PR.
5. **Abra um Pull Request** explicando o que mudou e por quê.

---

## 🛠️ Ambiente de Desenvolvimento

```bash
git clone https://github.com/Felipe-Alcantara/notion-workspace-app.git
cd notion-workspace-app
python start_app.py            # menu: instala, configura e sobe tudo

# Gate Python (HTTP mockado — não precisa de token nem rede)
pip install -r requirements.txt
ruff check .
python -m pytest

# Gate do front (SPA React)
cd front
npm install
npm run lint
npm run build
```

Requer Python 3.10+ e Node 22+. Copie `.env.example` para `.env` só para uso real
contra um workspace do Notion — nunca versione o `.env`.

---

## ✅ Padrões de Qualidade

- **Entenda o padrão existente antes de alterar.** Camadas do servidor:
  `config/` (projeto Django), `core/` (config por ambiente), `integrations/`
  (adaptadores), `services/` (casos de uso), `api/` (views finas), `operations/`
  (estado operacional SQLite). Fronteira sagrada: `api` não tem regra de negócio,
  `services` não conhece HTTP, só o `NotionClient` fala com a API do Notion.
- **A regra de negócio compartilhada vive no
  [`notion-starter`](https://github.com/Felipe-Alcantara/notion-starter)** —
  `integrations/github.py`, `integrations/openrouter.py` e os `services/` comuns
  aqui são shims; corrija a implementação real lá.
- **Preserve contratos.** Rotas REST, serializers, envelope de erro
  (`validacao/nao_encontrado/erro_upstream/erro_interno`) e ferramentas `notion.*`
  do MCP são consumidos por front e IAs; mudança quebradora precisa ser explícita.
- **Não exponha segredos.** Nada de tokens, IDs reais ou URLs privadas em código,
  testes ou documentação; SQLite operacional fora do git.
- **Teste o comportamento.** Bugs corrigidos viram regressão; HTTP mockado com
  `responses`, serviços com dependências injetadas.
- **Código, docstrings e mensagens de erro em português.**
- **Atualize a documentação viva** (`README.md` e `IA.md`) no mesmo passo.

---

## ✍️ Padrões de Linguagem (Documentação e Logs)

- Linguagem geral e acessível, sem jargão interno.
- Sem valores hardcoded — placeholders genéricos em vez de caminhos/tokens reais.
- Trabalho futuro como convite à contribuição, não lista de tarefas interna.

---

## 🔄 Fluxo de Pull Request

Um bom PR responde: **o que mudou**, **por que mudou**, **como foi validado**
(ex.: `ruff check .` + `python -m pytest` + `npm run lint` + `npm run build`) e
**qual risco sobrou**. Commits pequenos no formato `tipo: descrição`
(`feat`/`fix`/`docs`/`refactor`/`chore`).

---

## 💬 Código de Conduta

Seja respeitoso e acolhedor. Contribuições de pessoas de todos os níveis de
experiência são bem-vindas.
