"""Serialização da borda HTTP: objetos de domínio → dicts prontos para JSON.

Mantém as views finas e o contrato de saída num lugar só. Não expõe o JSON cru
do Notion (o campo ``bruto`` da :class:`Tarefa` fica fora da resposta pública).
"""

from __future__ import annotations

from typing import Any

from notion_starter import Tarefa


def tarefa_para_dict(tarefa: Tarefa) -> dict[str, Any]:
    """Converte uma :class:`Tarefa` no objeto JSON público da API (sem ``bruto``)."""

    return {
        "id": tarefa.id,
        "nome": tarefa.nome,
        "status": tarefa.status,
        "prazo": tarefa.prazo,
        "duracao": tarefa.duracao,
        "areas": tarefa.areas,
        "areas_nomes": tarefa.areas_nomes,
        "url": tarefa.url,
    }
