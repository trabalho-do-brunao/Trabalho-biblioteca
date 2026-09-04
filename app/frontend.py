"""Entrega do frontend React compilado quando a aplicação roda em produção.

No desenvolvimento, o Vite continua sendo executado separadamente em :5173.
Dentro da imagem Docker, o build do Vite é copiado para ``frontend_dist`` e
servido pelo próprio FastAPI, mantendo frontend e API na mesma origem.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIST = PROJECT_ROOT / "frontend_dist"


def _dist_path() -> Path:
    configurado = (os.getenv("FRONTEND_DIST_PATH") or "").strip()
    return Path(configurado).resolve() if configurado else DEFAULT_DIST.resolve()


def configurar_frontend_producao(app: FastAPI) -> bool:
    """Registra o fallback SPA quando existe um build de produção do React.

    Retorna ``True`` quando o frontend foi encontrado e configurado. Em ambiente
    local, onde ``frontend_dist`` normalmente não existe, retorna ``False`` e não
    interfere nas rotas da API nem no servidor Vite.
    """
    dist = _dist_path()
    index = dist / "index.html"

    if not index.is_file():
        return False

    @app.get("/{caminho:path}", include_in_schema=False)
    async def servir_frontend(caminho: str):
        # Rotas /api nunca devem cair no index.html. As rotas específicas da API
        # são registradas antes deste fallback; isto cobre apenas APIs inexistentes.
        if caminho == "api" or caminho.startswith("api/"):
            raise HTTPException(status_code=404, detail="Recurso da API não encontrado.")

        alvo = (dist / caminho).resolve()
        try:
            alvo.relative_to(dist)
        except ValueError as erro:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado.") from erro

        if caminho and alvo.is_file():
            return FileResponse(alvo)

        # React Router: /dashboard, /usuarios etc. recebem sempre o index.html.
        return FileResponse(index)

    return True
