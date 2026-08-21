"""Inicializa o banco PostgreSQL do BiblioAvisa.

Fluxo:
1. Carrega as configurações do arquivo .env.
2. Cria o banco definido em DB_NAME caso ele ainda não exista.
3. Executa database/db.sql quando o banco ainda não possui as tabelas do projeto.
4. Executa database/seed.sql para inserir os dados de demonstração.
5. Valida se as tabelas principais foram criadas.

O script não apaga tabelas ou dados existentes.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "database" / "db.sql"
SEED_PATH = PROJECT_ROOT / "database" / "seed.sql"
ENV_PATH = PROJECT_ROOT / ".env"

REQUIRED_TABLES = {
    "usuarios",
    "livros",
    "emprestimos",
    "renovacoes",
    "mensagens",
}


def carregar_configuracao() -> dict[str, str]:
    """Carrega e valida as variáveis necessárias para acessar o PostgreSQL."""
    if not ENV_PATH.exists():
        raise RuntimeError(
            "Arquivo .env não encontrado. Copie .env.example para .env e "
            "preencha os dados do seu PostgreSQL local."
        )

    load_dotenv(ENV_PATH)

    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "").strip(),
        "user": os.getenv("DB_USER", "").strip(),
        "password": os.getenv("DB_PASSWORD", ""),
        "maintenance_db": os.getenv("DB_MAINTENANCE_NAME", "postgres").strip()
        or "postgres",
    }

    faltando = [
        nome
        for nome, valor in {
            "DB_NAME": config["dbname"],
            "DB_USER": config["user"],
            "DB_PASSWORD": config["password"],
        }.items()
        if not valor
    ]

    if faltando:
        raise RuntimeError(
            "Preencha no arquivo .env: " + ", ".join(faltando)
        )

    return config


def conectar(config: dict[str, str], database: str):
    """Abre uma conexão com o PostgreSQL."""
    return psycopg2.connect(
        host=config["host"],
        port=config["port"],
        dbname=database,
        user=config["user"],
        password=config["password"],
    )


def garantir_banco(config: dict[str, str]) -> None:
    """Cria DB_NAME quando ele ainda não existir."""
    print(f"[INFO] Verificando banco '{config['dbname']}'...")

    try:
        conexao = conectar(config, config["maintenance_db"])
    except psycopg2.Error as erro:
        raise RuntimeError(
            "Não foi possível conectar ao PostgreSQL para verificar o banco. "
            "Confirme host, porta, usuário, senha e se o serviço PostgreSQL está ativo."
        ) from erro

    try:
        conexao.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conexao.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s;",
                (config["dbname"],),
            )
            existe = cursor.fetchone() is not None

            if existe:
                print(f"[OK] Banco '{config['dbname']}' já existe.")
                return

            print(f"[INFO] Criando banco '{config['dbname']}'...")
            cursor.execute(
                sql.SQL("CREATE DATABASE {};").format(
                    sql.Identifier(config["dbname"])
                )
            )
            print(f"[OK] Banco '{config['dbname']}' criado.")
    except psycopg2.Error as erro:
        raise RuntimeError(
            "Não foi possível criar o banco. O usuário configurado em DB_USER "
            "precisa ter permissão para criar bancos, ou o banco deve ser criado "
            "manualmente uma única vez no pgAdmin."
        ) from erro
    finally:
        conexao.close()


def listar_tabelas(conexao) -> set[str]:
    """Retorna as tabelas do schema public."""
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public';
            """
        )
        return {linha[0] for linha in cursor.fetchall()}


def executar_arquivo_sql(conexao, caminho: Path, descricao: str) -> None:
    """Executa um arquivo SQL inteiro dentro de uma transação."""
    if not caminho.exists():
        raise RuntimeError(f"Arquivo não encontrado: {caminho}")

    conteudo = caminho.read_text(encoding="utf-8")
    print(f"[INFO] Executando {descricao}: {caminho.relative_to(PROJECT_ROOT)}")

    try:
        with conexao.cursor() as cursor:
            cursor.execute(conteudo)
        conexao.commit()
        print(f"[OK] {descricao} executado com sucesso.")
    except psycopg2.Error:
        conexao.rollback()
        raise


def preparar_estrutura(conexao) -> None:
    """Cria o schema quando vazio e detecta estruturas parciais/incompatíveis."""
    tabelas_existentes = listar_tabelas(conexao)
    tabelas_projeto = tabelas_existentes & REQUIRED_TABLES

    if not tabelas_projeto:
        executar_arquivo_sql(conexao, SCHEMA_PATH, "estrutura do banco")
        return

    if REQUIRED_TABLES.issubset(tabelas_existentes):
        print("[OK] As tabelas principais já existem; db.sql não será executado novamente.")
        return

    faltando = sorted(REQUIRED_TABLES - tabelas_existentes)
    raise RuntimeError(
        "O banco possui apenas parte da estrutura do BiblioAvisa. "
        "Tabelas faltando: " + ", ".join(faltando) + ". "
        "Para evitar apagar dados automaticamente, o script foi interrompido."
    )


def validar_banco(conexao) -> None:
    """Confirma a existência das tabelas obrigatórias e mostra um resumo."""
    tabelas = listar_tabelas(conexao)
    faltando = REQUIRED_TABLES - tabelas

    if faltando:
        raise RuntimeError(
            "Inicialização incompleta. Tabelas faltando: "
            + ", ".join(sorted(faltando))
        )

    print("\n[OK] Banco BiblioAvisa validado.")
    print("[OK] Tabelas encontradas:")
    for tabela in sorted(REQUIRED_TABLES):
        print(f"     - {tabela}")


def main() -> int:
    print("=== Inicialização do banco BiblioAvisa ===\n")

    try:
        config = carregar_configuracao()
        garantir_banco(config)

        print(f"[INFO] Conectando ao banco '{config['dbname']}'...")
        with conectar(config, config["dbname"]) as conexao:
            print("[OK] Conexão realizada com sucesso.")
            preparar_estrutura(conexao)
            executar_arquivo_sql(conexao, SEED_PATH, "dados de demonstração")
            validar_banco(conexao)

        print("\n=== Inicialização concluída com sucesso ===")
        return 0

    except (RuntimeError, psycopg2.Error) as erro:
        print(f"\n[ERRO] {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
