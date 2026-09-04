"""Ponto de entrada WSGI do servidor (deploy com gunicorn/uwsgi)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

_SERVER_DIR = Path(__file__).resolve().parent.parent
if str(_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVER_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
