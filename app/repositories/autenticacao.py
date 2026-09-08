"""Persistência da autenticação administrativa do BiblioAvisa."""

from __future__ import annotations

from datetime import date, datetime

import psycopg2
from psycopg2.extras import RealDictCursor

from app.db import conectar


def contar_administradores() -> int:
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM administradores;")
            return int(cursor.fetchone()[0])
    finally:
        conexao.close()


def buscar_administrador_por_email(email: str) -> dict[str, object] | None:
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    nome,
                    sobrenome,
                    cpf,
                    data_nascimento,
                    whatsapp,
                    email,
                    senha_hash,
                    ativo,
                    criado_em,
                    atualizado_em
                FROM administradores
                WHERE LOWER(email) = LOWER(%s)
                LIMIT 1;
                """,
                (email,),
            )
            linha = cursor.fetchone()
            return dict(linha) if linha else None
    finally:
        conexao.close()


def criar_administrador(
    nome: str,
    email: str,
    senha_hash: str,
    *,
    sobrenome: str | None = None,
    cpf: str | None = None,
    data_nascimento: date | None = None,
    whatsapp: str | None = None,
) -> dict[str, object]:
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO administradores (
                    nome,
                    sobrenome,
                    cpf,
                    data_nascimento,
                    whatsapp,
                    email,
                    senha_hash
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    nome,
                    sobrenome,
                    cpf,
                    data_nascimento,
                    whatsapp,
                    email,
                    ativo,
                    criado_em,
                    atualizado_em;
                """,
                (nome, sobrenome, cpf, data_nascimento, whatsapp, email, senha_hash),
            )
            linha = cursor.fetchone()
        conexao.commit()
        return dict(linha)
    except psycopg2.errors.UniqueViolation as erro:
        conexao.rollback()
        nome_constraint = str(getattr(erro.diag, "constraint_name", "") or "")
        if "cpf" in nome_constraint:
            raise ValueError("Já existe uma conta administrativa com esse CPF.") from erro
        raise ValueError("Já existe uma conta administrativa com esse e-mail.") from erro
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def limpar_sessoes_expiradas() -> int:
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM sessoes_admin WHERE expira_em <= NOW();")
            removidas = cursor.rowcount
        conexao.commit()
        return removidas
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def criar_sessao(
    administrador_id: int,
    token_hash: str,
    expira_em: datetime,
) -> None:
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM sessoes_admin WHERE expira_em <= NOW();")
            cursor.execute(
                """
                INSERT INTO sessoes_admin (administrador_id, token_hash, expira_em)
                VALUES (%s, %s, %s);
                """,
                (administrador_id, token_hash, expira_em),
            )
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def buscar_administrador_por_sessao(token_hash: str) -> dict[str, object] | None:
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    a.id,
                    a.nome,
                    a.sobrenome,
                    a.email,
                    a.ativo,
                    s.expira_em
                FROM sessoes_admin s
                INNER JOIN administradores a ON a.id = s.administrador_id
                WHERE s.token_hash = %s
                  AND s.expira_em > NOW()
                  AND a.ativo = TRUE
                LIMIT 1;
                """,
                (token_hash,),
            )
            linha = cursor.fetchone()
            if not linha:
                return None

            cursor.execute(
                """
                UPDATE sessoes_admin
                SET ultimo_uso_em = NOW()
                WHERE token_hash = %s;
                """,
                (token_hash,),
            )
        conexao.commit()
        return dict(linha)
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def encerrar_sessao(token_hash: str) -> None:
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                "DELETE FROM sessoes_admin WHERE token_hash = %s;",
                (token_hash,),
            )
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()
