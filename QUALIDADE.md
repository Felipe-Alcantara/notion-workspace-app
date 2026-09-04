# ✅ Qualidade — notion-workspace-app

Este documento registra o gate de qualidade do módulo e as exceções motivadas ao
[Felixo System Design](https://github.com/Felipe-Alcantara/Felixo-System-Design).

## Gate local

Na raiz, execute o gate Python:

```bash
python -m ruff check .
python -m pytest
```

Em `front/`, execute o gate da SPA:

```bash
npm run lint
npm run build
```

A CI em `.github/workflows/ci.yml` executa o backend em Python 3.10–3.13 e o
frontend em Node 22 com instalação reproduzível por `npm ci`.

## Critério de pronto

Uma mudança está pronta quando:

- lint, testes Python e build do frontend passam;
- contratos REST, MCP e fronteiras de camada foram preservados ou documentados;
- nenhum segredo, ID real ou banco SQLite foi versionado;
- README, `IA.md`, testes e contrato de interface foram atualizados quando
  afetados;
- riscos ou limitações restantes foram registrados.

## Dependências e distribuição

O `pyproject.toml` é a fonte canônica do pacote e separa dependências de runtime
das ferramentas de desenvolvimento no extra `dev`. O `requirements.txt` mantém
um espelho simples para o fluxo de desenvolvimento legado, sem URL Git.

Os limites mínimos (`>=`) mantêm compatibilidade entre Python 3.10–3.13 e com a
biblioteca compartilhada `notion-starter`; essa é uma exceção deliberada à
recomendação geral de pins exatos e é exercitada pela matriz da CI.

O risco de novas versões compatíveis alterarem o ambiente é aceito e monitorado
pela CI. O frontend não usa essa exceção: `front/package-lock.json` está
versionado e `npm ci` instala a resolução registrada.

O workflow de release compila a SPA para `server/static/frontend/`, valida wheel
e sdist com `twine check` e executa smoke nos três sistemas suportados. O launcher
detecta a instalação empacotada e serve o bundle via Django sem consultar
Node/npm. A versão candidata atual é `0.3.0`; publicação e Trusted Publishing
aguardam a confirmação de nome, ownership e metadados legais.
