#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
COMPOSE_FILE="$ROOT/docker-compose.aws.yml"
SUDO=()
ACAO="${1:-start}"

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERRO] Docker não encontrado. Execute primeiro: bash setup_linux.sh" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "[ERRO] Docker Compose v2 não encontrado. Execute primeiro: bash setup_linux.sh" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  if sudo docker info >/dev/null 2>&1; then
    SUDO=(sudo)
  else
    echo "[ERRO] O serviço Docker não está disponível." >&2
    exit 1
  fi
fi

dc() {
  "${SUDO[@]}" docker compose -f "$COMPOSE_FILE" "$@"
}

if [[ ! -f .env ]]; then
  echo "[ERRO] .env não encontrado. Execute primeiro: bash setup_linux.sh" >&2
  exit 1
fi

ler_env() {
  local nome="$1"
  local padrao="$2"
  local valor
  valor="$(grep -E "^${nome}=" .env | tail -n 1 | cut -d= -f2- || true)"
  printf '%s' "${valor:-$padrao}"
}

esta_ativo() {
  local valor
  valor="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | xargs)"
  [[ "$valor" == "1" || "$valor" == "true" || "$valor" == "yes" || "$valor" == "sim" || "$valor" == "on" ]]
}

esperar_db() {
  local db_user db_name
  db_user="$(ler_env DB_USER postgres)"
  db_name="$(ler_env DB_NAME ecf)"

  for tentativa in $(seq 1 30); do
    if dc exec -T db pg_isready -U "$db_user" -d "$db_name" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done

  echo "[ERRO] PostgreSQL não ficou pronto dentro do tempo esperado." >&2
  dc logs db --tail=80 || true
  return 1
}

esperar_api() {
  for tentativa in $(seq 1 30); do
    if dc exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2).read()" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  echo "[ERRO] A API não respondeu ao health check dentro do tempo esperado." >&2
  echo "[INFO] Estado atual dos containers:" >&2
  dc ps || true
  echo "[INFO] Últimos logs da API:" >&2
  dc logs api --tail=100 || true
  return 1
}

iniciar() {
  echo "[INFO] Construindo/atualizando imagens..."
  dc build

  echo "[INFO] Iniciando PostgreSQL..."
  dc up -d db
  esperar_db

  echo "[INFO] Aplicando estrutura e migrações do banco..."
  dc run --rm api python scripts/init_db.py

  echo "[INFO] Iniciando API, webhook e Baileys..."
  dc up -d api webhook baileys
  esperar_api

  local automacao
  automacao="$(ler_env AUTOMACAO_ENABLED false)"
  if esta_ativo "$automacao"; then
    echo "[INFO] Automação diária ativada no .env; iniciando agendador..."
    dc up -d automation
  else
    echo "[INFO] Automação diária desativada no .env."
    dc stop automation >/dev/null 2>&1 || true
    dc rm -f automation >/dev/null 2>&1 || true
  fi

  local porta_http
  porta_http="$(ler_env BIBLIOAVISA_HTTP_PORT 8000)"

  echo
  echo "======================================================"
  echo "[OK] BiblioAvisa iniciado na AWS/Linux."
  echo "======================================================"
  echo "Aplicação: http://IP_PUBLICO_DA_VM:${porta_http}"
  echo
  echo "Status:"
  dc ps
  echo
  echo "Para acompanhar todos os logs:"
  echo "  bash run_linux.sh logs"
  echo
  echo "Para acompanhar apenas o QR/WhatsApp:"
  echo "  ${SUDO[*]} docker compose -f docker-compose.aws.yml logs -f baileys"
  echo
  echo "Para parar o sistema:"
  echo "  bash run_linux.sh stop"
}

case "$ACAO" in
  start)
    iniciar
    ;;
  restart)
    dc down
    iniciar
    ;;
  stop)
    dc down
    echo "[OK] Containers encerrados. Os volumes persistentes foram preservados."
    ;;
  logs)
    dc logs -f --tail=150
    ;;
  status)
    dc ps
    ;;
  *)
    echo "Uso: bash run_linux.sh [start|restart|stop|logs|status]" >&2
    exit 2
    ;;
esac
