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

## Exceção motivada: dependências Python

O `requirements.txt` usa limites mínimos (`>=`) para manter compatibilidade entre
Python 3.10–3.13 e com a biblioteca compartilhada `notion-starter`. Esta é uma
exceção deliberada à recomendação geral de pins exatos; a resolução é exercitada
continuamente pela matriz da CI.

O risco de novas versões compatíveis alterarem o ambiente é aceito e monitorado
pela CI. O frontend não usa essa exceção: `front/package-lock.json` está
versionado e `npm ci` instala a resolução registrada.
