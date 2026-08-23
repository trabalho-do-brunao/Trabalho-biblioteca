"""Conexão central da aplicação com o PostgreSQL.

Este módulo concentra a leitura das variáveis do arquivo .env e a criação
de conexões com o banco configurado em DB_NAME.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection as PostgreSQLConnection
from psycopg2.extras import RealDictCursor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"


def carregar_configuracao() -> dict[str, str]:
    """Carrega e valida as configurações necessárias para o PostgreSQL."""
    if not ENV_PATH.exists():
        raise RuntimeError(
            "Arquivo .env não encontrado. Execute setup.bat ou copie "
            ".env.example para .env e configure o PostgreSQL."
        )

    load_dotenv(ENV_PATH)

    configuracao = {
        "host": os.getenv("DB_HOST", "localhost").strip(),
        "port": os.getenv("DB_PORT", "5432").strip(),
        "dbname": os.getenv("DB_NAME", "").strip(),
        "user": os.getenv("DB_USER", "").strip(),
        "password": os.getenv("DB_PASSWORD", ""),
    }

    obrigatorias = {
        "DB_NAME": configuracao["dbname"],
        "DB_USER": configuracao["user"],
        "DB_PASSWORD": configuracao["password"],
    }
    faltando = [nome for nome, valor in obrigatorias.items() if not valor]

    if faltando:
        raise RuntimeError(
            "Variáveis obrigatórias não configuradas no .env: "
            + ", ".join(faltando)
        )

    return configuracao


def conectar() -> PostgreSQLConnection:
    """Abre e retorna uma conexão com o PostgreSQL configurado no .env."""
    configuracao = carregar_configuracao()

    try:
        return psycopg2.connect(**configuracao)
    except psycopg2.Error as erro:
        raise ConnectionError(
            "Não foi possível conectar ao PostgreSQL. Confira o arquivo .env "
            "e se o serviço PostgreSQL está em execução."
        ) from erro


def testar_conexao() -> dict[str, dict[str, object]]:
    """Testa a conexão e retorna informações simples do banco para diagnóstico."""
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    current_database() AS banco,
                    current_user AS usuario,
                    version() AS versao;
                """
            )
            informacoes = dict(cursor.fetchone())

            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM usuarios) AS usuarios,
                    (SELECT COUNT(*) FROM livros) AS livros,
                    (SELECT COUNT(*) FROM emprestimos) AS emprestimos,
                    (SELECT COUNT(*) FROM renovacoes) AS renovacoes,
                    (SELECT COUNT(*) FROM mensagens) AS mensagens;
                """
            )
            registros = dict(cursor.fetchone())

        return {
            "conexao": informacoes,
            "registros": registros,
        }
    finally:
        conexao.close()
