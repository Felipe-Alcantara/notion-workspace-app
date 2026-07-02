#!/usr/bin/env python3
"""Utilitário de linha de comando do Django para tarefas administrativas.

Roda a partir de ``server/`` (este diretório entra no ``sys.path``, então
``config``, ``core``, ``api`` etc. importam como pacotes de topo).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    # Garante que ``server/`` esteja no path para importar os pacotes de camada.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover - mensagem de ajuda
        raise ImportError(
            "Django não está instalado. Instale os extras de servidor com:\n"
            '  pip install -e ".[server]"'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
