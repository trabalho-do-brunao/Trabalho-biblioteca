"""Valida que o inicializador Linux/AWS publica o sistema via Nginx."""
from pathlib import Path


conteudo = Path("run_linux.sh").read_text(encoding="utf-8")
env_exemplo = Path(".env.example").read_text(encoding="utf-8")

assert "dc up -d api webhook baileys nginx" in conteudo, "run_linux.sh deve iniciar o Nginx"
assert "ler_env BIBLIOAVISA_HTTP_PORT 80" in conteudo, "porta HTTP padrão deve ser 80"
assert "esperar_gateway" in conteudo, "run_linux.sh deve validar o gateway Nginx"
assert "BIBLIOAVISA_HTTP_PORT=80" in env_exemplo, ".env.example deve usar porta 80 por padrão"

print("[OK] Inicializador Linux/AWS configurado para Nginx na porta 80.")
