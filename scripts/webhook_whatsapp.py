"""Inicia o webhook local usado pelo serviço Baileys."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.webhooks.whatsapp import executar_servidor


if __name__ == "__main__":
    executar_servidor()
