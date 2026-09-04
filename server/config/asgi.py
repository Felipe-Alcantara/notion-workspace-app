"""Ponto de entrada ASGI do servidor (deploy assíncrono / websockets futuros)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application

_SERVER_DIR = Path(__file__).resolve().parent.parent
if str(_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVER_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
