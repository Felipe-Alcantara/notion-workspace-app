"""Configuração de testes compartilhada.

Adiciona a raiz do repositório e ``server/`` ao ``sys.path`` para que os
testes consigam importar ``start_app`` e os pacotes da camada de servidor
(``api``, ``services``, ``core``…) como o Django faz ao rodar a partir de
``server/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SERVER = _ROOT / "server"

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if _SERVER.exists() and str(_SERVER) not in sys.path:
    sys.path.insert(0, str(_SERVER))
