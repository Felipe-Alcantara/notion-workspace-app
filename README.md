# 🧭 notion-workspace-app

<div align="center">

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django 5+](https://img.shields.io/badge/Django-5%2B-092E20?style=for-the-badge&logo=django&logoColor=white)
![React 18](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite 8](https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Licença MIT](https://img.shields.io/badge/Licen%C3%A7a-MIT-green?style=for-the-badge)

**Aplicação local completa para operar o Notion com API Django, SPA React, servidor MCP e launcher TUI.**

[📖 Sobre](#-sobre-o-projeto) • [🚀 Componentes](#-componentes) • [🎯 Como usar](#-como-usar) • [✅ Qualidade](#-qualidade)

</div>

---

## 📋 Índice

- [📖 Sobre o Projeto](#-sobre-o-projeto)
- [📁 Estrutura do Projeto](#-estrutura-do-projeto)
- [🚀 Componentes](#-componentes)
- [✨ Funcionalidades](#-funcionalidades)
- [🎯 Como Usar](#-como-usar)
- [🔐 Configuração e Segurança](#-configuração-e-segurança)
- [✅ Qualidade](#-qualidade)
- [📄 Licença](#-licença)
- [👤 Autor](#-autor)
- [🤝 Contribuições](#-contribuições)

---

## 📖 Sobre o Projeto

O `notion-workspace-app` reúne quatro interfaces sobre o mesmo núcleo de dados:
uma **API REST Django**, uma **SPA React**, um **servidor MCP** para clientes de IA
e um **launcher TUI** que prepara e inicia o ambiente. A aplicação permite
gerenciar tarefas em kanban, grade ou lista, explorar o workspace e sincronizar
repositórios do GitHub com databases do Notion.

A regra de negócio compartilhada vem da biblioteca
[notion-starter](https://github.com/Felipe-Alcantara/notion-starter). Este
repositório mantém as bordas Django, React e MCP, além da configuração específica
do produto. A porta de entrada recomendada é `python start_app.py`.

O projeto integra o ecossistema
[Automações do Notion](https://github.com/Felipe-Alcantara/Automa-es-do-Notion).

---

## 📁 Estrutura do Projeto

```text
notion-workspace-app/
│
├── 📁 server/                   # Backend Django e servidor MCP
│   ├── 📁 api/                  # Views, serializers e rotas REST
│   ├── 📁 config/               # Configuração do projeto Django
│   ├── 📁 integrations/         # Notion local e shims de adaptadores
│   ├── 📁 operations/           # Estado operacional em SQLite
│   ├── 📁 services/             # Shims dos casos de uso compartilhados
│   └── mcp_server.py            # Ferramentas notion.*
│
├── 📁 front/                    # SPA React com Vite
│   ├── 📁 src/components/       # Interface, tarefas e exploração
│   ├── 📁 src/hooks/            # Estado e acesso à API
│   └── package-lock.json        # Resolução reproduzível do frontend
│
├── 📁 tests/                    # Suíte Python automatizada
├── .github/workflows/ci.yml     # Gates Python e frontend
├── start_app.py                 # Menu interativo de entrada
├── requirements.txt             # Dependências Python
├── QUALIDADE.md                 # Contrato de qualidade do módulo
├── README.md                    # Este arquivo
└── LICENSE                      # Licença MIT
```

---

## 🚀 Componentes

| Camada | Pasta | Descrição |
| --- | --- | --- |
| Launcher | `start_app.py` | TUI que instala dependências, configura e sobe servidor e front |
| API | `server/api/` | REST Django para tarefas, exploração e opções |
| Services | `server/services/` | Shims para tarefas, clonagem, ingestão, IA e GitHub |
| Integrações | `server/integrations/` | Notion local e shims para GitHub/OpenRouter |
| MCP | `server/mcp_server.py` | Servidor que expõe operações `notion.*` para IAs |
| Front | `front/` | SPA React com kanban, filtros e exploração do workspace |

---

## ✨ Funcionalidades

- visualizar tarefas em kanban, grade e lista;
- buscar e filtrar tarefas por status, duração e área;
- criar e editar tarefas pela interface;
- explorar páginas e databases compartilhados;
- sincronizar repositórios GitHub com databases do Notion;
- expor operações para clientes de IA via MCP;
- iniciar Django e Vite em conjunto pelo launcher interativo.

Exemplo de fluxo: ação na SPA → API Django → serviço compartilhado → API do
Notion.

---

## 🎯 Como Usar

### Início rápido

```bash
# Clone o repositório
git clone https://github.com/Felipe-Alcantara/notion-workspace-app.git
cd notion-workspace-app

# Instale as dependências Python
pip install -r requirements.txt

# Crie a configuração local e preencha os valores necessários
cp .env.example .env

# Abra o menu que instala, configura e inicia o produto
python start_app.py
```

O launcher aplica as migrações, sobe Django e Vite e abre o navegador. Pelo menu
também é possível instalar dependências, configurar o ambiente e conferir o
status dos componentes.

---

## 🔐 Configuração e Segurança

Use `.env.example` como modelo e mantenha o `.env` apenas na máquina local. Para
operar o workspace, configure `NOTION_TOKEN` e, quando aplicável,
`NOTION_DATABASE_ID`.

Nunca versione tokens, IDs reais ou bancos SQLite. Os testes usam mocks e não
dependem de credenciais reais.

---

## ✅ Qualidade

Gate Python, executado na raiz:

```bash
python -m ruff check .
python -m pytest
```

Gate da SPA:

```bash
cd front
npm run lint
npm run build
```

A CI executa Python 3.10–3.13 e um job Node 22 com `npm ci`. Consulte
[`QUALIDADE.md`](QUALIDADE.md) para o critério de pronto e a política de
dependências.

---

## 📄 Licença

Este projeto está sob a licença MIT — veja [`LICENSE`](LICENSE).

---

## 👤 Autor

**Felipe Martin**

- GitHub: [@Felipe-Alcantara](https://github.com/Felipe-Alcantara)
- Repositório: [notion-workspace-app](https://github.com/Felipe-Alcantara/notion-workspace-app)

---

## 🤝 Contribuições

Contribuições são bem-vindas. Algumas ideias para quem quiser colaborar:

- ampliar a escrita genérica na aba Explorar;
- criar novas visualizações e interações no kanban;
- melhorar o empacotamento do launcher;
- expandir acessibilidade, testes e documentação.

Leia [`CONTRIBUTING.md`](CONTRIBUTING.md) antes de enviar uma mudança.

---

⭐ Se o app foi útil, considere dar uma estrela no
[GitHub](https://github.com/Felipe-Alcantara/notion-workspace-app).
