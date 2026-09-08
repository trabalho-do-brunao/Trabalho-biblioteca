#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
COMPOSE_FILE="$ROOT/docker-compose.aws.yml"
SUDO=()

info() { printf '[INFO] %s\n' "$*"; }
ok() { printf '[OK] %s\n' "$*"; }
erro() { printf '[ERRO] %s\n' "$*" >&2; }

instalar_docker() {
  info "Docker não encontrado. Instalando pacotes do Ubuntu..."
  sudo apt-get update
  sudo apt-get install -y docker.io
  sudo systemctl enable --now docker
}

if ! command -v docker >/dev/null 2>&1; then
  instalar_docker
fi

if ! docker compose version >/dev/null 2>&1; then
  info "Docker Compose v2 não encontrado. Tentando instalar..."
  sudo apt-get update
  if ! sudo apt-get install -y docker-compose-v2; then
    sudo apt-get install -y docker-compose-plugin
  fi
fi

if ! docker compose version >/dev/null 2>&1; then
  erro "Docker Compose v2 não está disponível. Instale o plugin 'docker compose' e execute novamente."
  exit 1
fi

sudo systemctl enable --now docker >/dev/null 2>&1 || true

if ! docker info >/dev/null 2>&1; then
  if sudo docker info >/dev/null 2>&1; then
    SUDO=(sudo)
  else
    erro "O serviço Docker não está disponível."
    exit 1
  fi
fi

dc() {
  "${SUDO[@]}" docker compose -f "$COMPOSE_FILE" "$@"
}

if [[ ! -f "$COMPOSE_FILE" ]]; then
  erro "docker-compose.aws.yml não encontrado."
  exit 1
fi

if [[ ! -f .env ]]; then
  if [[ ! -f .env.example ]]; then
    erro ".env.example não encontrado."
    exit 1
  fi

  cp .env.example .env
  chmod 600 .env
  printf '\n[ATENÇÃO] O arquivo .env foi criado.\n'
  printf 'Edite as configurações locais da VM, principalmente DB_PASSWORD e credenciais opcionais.\n'
  printf 'Exemplo: nano .env\n\n'
  printf 'Depois execute novamente: bash setup_linux.sh\n'
  exit 2
fi

chmod 600 .env

DB_PASSWORD_VALUE="$(grep -E '^DB_PASSWORD=' .env | tail -n 1 | cut -d= -f2- || true)"
if [[ -z "$DB_PASSWORD_VALUE" || "$DB_PASSWORD_VALUE" == "preencha_localmente" || "$DB_PASSWORD_VALUE" == "troque_esta_senha" ]]; then
  erro "DB_PASSWORD ainda não foi configurado no .env."
  echo "Edite com: nano .env"
  exit 1
fi

DB_USER_VALUE="$(grep -E '^DB_USER=' .env | tail -n 1 | cut -d= -f2- || true)"
DB_NAME_VALUE="$(grep -E '^DB_NAME=' .env | tail -n 1 | cut -d= -f2- || true)"
DB_USER_VALUE="${DB_USER_VALUE:-postgres}"
DB_NAME_VALUE="${DB_NAME_VALUE:-ecf}"

info "Validando configuração Docker Compose..."
dc config -q
ok "Configuração Docker Compose válida."

info "Construindo as imagens do BiblioAvisa..."
dc build
ok "Imagens construídas."

info "Iniciando PostgreSQL temporariamente para preparar o banco..."
dc up -d db

for tentativa in $(seq 1 30); do
  if dc exec -T db pg_isready -U "$DB_USER_VALUE" -d "$DB_NAME_VALUE" >/dev/null 2>&1; then
    break
  fi

  if [[ "$tentativa" -eq 30 ]]; then
    erro "PostgreSQL não ficou pronto dentro do tempo esperado."
    dc logs db --tail=80 || true
    exit 1
  fi

  sleep 2
done

ok "PostgreSQL disponível."

info "Criando/atualizando tabelas e migrações..."
dc run --rm api python scripts/init_db.py
ok "Banco validado sem inserir dados de demonstração."

info "Encerrando os containers de preparação. Os volumes permanecem salvos."
dc down

printf '\n======================================================\n'
printf '[OK] Ambiente Linux/AWS preparado.\n'
printf '======================================================\n\n'
printf 'Para iniciar o sistema:\n'
printf '  bash run_linux.sh\n\n'
printf 'A porta pública padrão da aplicação é 8000.\n'
printf 'PostgreSQL, webhook e Baileys permanecem apenas na rede interna do Docker.\n'
