"""Endpoint HTTP local que recebe mensagens encaminhadas pelo serviço Baileys."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app.services.renovacao_whatsapp import processar_resposta_whatsapp


class WhatsAppWebhookHandler(BaseHTTPRequestHandler):
    server_version = "BiblioAvisaWebhook/1.0"

    def _responder(self, status: int, dados: dict[str, object]) -> None:
        corpo = json.dumps(dados, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._responder(200, {"ok": True, "service": "whatsapp-webhook"})
            return
        self._responder(404, {"ok": False, "error": "Rota não encontrada."})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/webhook/whatsapp":
            self._responder(404, {"ok": False, "error": "Rota não encontrada."})
            return

        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            if tamanho <= 0 or tamanho > 64 * 1024:
                raise ValueError("Corpo da requisição inválido ou muito grande.")

            dados = json.loads(self.rfile.read(tamanho).decode("utf-8"))
            telefone = str(dados.get("phone") or "").strip()
            mensagem = str(dados.get("message") or "").strip()
            identificador = str(dados.get("message_id") or "").strip()
            citado = str(dados.get("quoted_message_id") or "").strip() or None

            if not telefone or not mensagem or not identificador:
                raise ValueError("phone, message e message_id são obrigatórios.")

            resultado = processar_resposta_whatsapp(
                telefone=telefone,
                texto=mensagem,
                identificador_externo=identificador,
                mensagem_citada_id=citado,
            )
            self._responder(200, {"ok": True, "result": resultado})
        except (ValueError, json.JSONDecodeError) as erro:
            self._responder(400, {"ok": False, "error": str(erro)})
        except Exception as erro:
            print(f"[ERRO] Falha ao processar webhook do WhatsApp: {erro}")
            self._responder(500, {"ok": False, "error": "Falha interna ao processar a mensagem."})

    def log_message(self, format: str, *args: object) -> None:
        # Mantém o terminal limpo; erros relevantes são impressos explicitamente.
        return


def criar_servidor() -> ThreadingHTTPServer:
    host = (os.getenv("WHATSAPP_WEBHOOK_HOST") or "127.0.0.1").strip()
    porta = int((os.getenv("WHATSAPP_WEBHOOK_PORT") or "3002").strip())
    return ThreadingHTTPServer((host, porta), WhatsAppWebhookHandler)


def executar_servidor() -> None:
    servidor = criar_servidor()
    host, porta = servidor.server_address
    print(f"[OK] Webhook do WhatsApp em http://{host}:{porta}/webhook/whatsapp")
    print(f"[OK] Health em http://{host}:{porta}/health")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Encerrando webhook do WhatsApp...")
    finally:
        servidor.server_close()
