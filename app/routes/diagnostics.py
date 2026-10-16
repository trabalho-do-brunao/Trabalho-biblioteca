"""Diagnóstico não destrutivo de conectividade dos serviços internos.

A rota exige autenticação administrativa via app.api.
Não executa comandos, não lê mensagens nem altera o banco.
"""
from __future__ import annotations

import os
import socket
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["sistema"])

def _tcp(host: str, port: int) -> dict[str, object]:
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return {"status": "reachable"}
    except (OSError, ValueError):
        return {"status": "unreachable"}

def _endpoint(env_name: str, default: str) -> tuple[str, int]:
    parsed = urlsplit(os.getenv(env_name) or default)
    return parsed.hostname or "localhost", parsed.port or (443 if parsed.scheme == "https" else 80)

@router.get("/diagnostics")
def diagnostics() -> dict[str, object]:
    """Checagem TCP leve; alcançável não significa aplicação saudável."""
    db_host = os.getenv("DB_HOST") or "localhost"
    try:
        db_port = int(os.getenv("DB_PORT") or "5432")
        baileys = _endpoint("WHATSAPP_SERVICE_URL", "http://baileys:3001")
        webhook = _endpoint("WHATSAPP_WEBHOOK_URL", "http://webhook:3002/webhook/whatsapp")
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {
                "postgres": pool.submit(_tcp, db_host, db_port),
                "baileys": pool.submit(_tcp, *baileys),
                "webhook": pool.submit(_tcp, *webhook),
            }
            services = {name: future.result() for name, future in futures.items()}
    except (ValueError, OverflowError):
        return {"status": "configuration_error", "services": {}}
    return {
        "status": "reachable" if all(item["status"] == "reachable" for item in services.values()) else "degraded",
        "check_type": "tcp_connectivity_only",
        "services": services,
    }
