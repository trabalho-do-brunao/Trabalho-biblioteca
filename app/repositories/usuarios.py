"""Operações de banco relacionadas aos usuários da biblioteca."""

from __future__ import annotations

import re

import psycopg2
from psycopg2.errors import UniqueViolation
from psycopg2.extras import RealDictCursor

from app.db import conectar


class UsuarioDuplicadoError(ValueError):
    """Indica tentativa de cadastrar um telefone que já existe."""


def validar_nome(nome: str) -> str:
    """Normaliza e valida o nome informado pelo usuário."""
    nome_limpo = " ".join((nome or "").split())

    if len(nome_limpo) < 2:
        raise ValueError("O nome deve possuir pelo menos 2 caracteres.")

    if len(nome_limpo) > 150:
        raise ValueError("O nome deve possuir no máximo 150 caracteres.")

    return nome_limpo


def normalizar_telefone(telefone: str) -> str:
    """Retorna o telefone somente com dígitos e código do país.

    Para números brasileiros com DDD informados sem o código do país,
    acrescenta automaticamente o código 55. O formato armazenado serve
    como base para a futura integração com provedores de WhatsApp.
    """
    digitos = re.sub(r"\D", "", telefone or "")

    if digitos.startswith("00"):
        digitos = digitos[2:]

    if len(digitos) in (10, 11):
        digitos = "55" + digitos

    if not 12 <= len(digitos) <= 15:
        raise ValueError(
            "Telefone inválido. Informe DDD e número; o código 55 pode ser omitido para números brasileiros."
        )

    return digitos


def normalizar_email(email: str | None) -> str | None:
    """Normaliza um e-mail opcional e faz uma validação básica."""
    if email is None or not email.strip():
        return None

    email_limpo = email.strip().lower()

    if len(email_limpo) > 150 or "@" not in email_limpo:
        raise ValueError("E-mail inválido.")

    return email_limpo


def cadastrar_usuario(
    nome: str,
    telefone: str,
    email: str | None = None,
) -> dict[str, object]:
    """Cadastra um usuário e retorna o registro criado."""
    nome_limpo = validar_nome(nome)
    telefone_normalizado = normalizar_telefone(telefone)
    email_normalizado = normalizar_email(email)

    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO usuarios (nome, telefone, email)
                VALUES (%s, %s, %s)
                RETURNING id, nome, telefone, email, ativo, criado_em;
                """,
                (nome_limpo, telefone_normalizado, email_normalizado),
            )
            usuario = dict(cursor.fetchone())

        conexao.commit()
        return usuario

    except UniqueViolation as erro:
        conexao.rollback()
        raise UsuarioDuplicadoError(
            "Já existe um usuário cadastrado com este telefone."
        ) from erro
    except psycopg2.Error as erro:
        conexao.rollback()
        raise RuntimeError("Não foi possível cadastrar o usuário.") from erro
    finally:
        conexao.close()


def buscar_usuario_por_id(usuario_id: int) -> dict[str, object] | None:
    """Busca um usuário pelo ID."""
    if not isinstance(usuario_id, int) or usuario_id <= 0:
        raise ValueError("O ID do usuário deve ser um número inteiro positivo.")

    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, nome, telefone, email, ativo, criado_em
                FROM usuarios
                WHERE id = %s;
                """,
                (usuario_id,),
            )
            registro = cursor.fetchone()
            return dict(registro) if registro else None
    finally:
        conexao.close()


def buscar_usuario_por_telefone(telefone: str) -> dict[str, object] | None:
    """Busca um usuário pelo telefone, aceitando telefone formatado ou somente dígitos."""
    telefone_normalizado = normalizar_telefone(telefone)
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, nome, telefone, email, ativo, criado_em
                FROM usuarios
                WHERE telefone = %s;
                """,
                (telefone_normalizado,),
            )
            registro = cursor.fetchone()
            return dict(registro) if registro else None
    finally:
        conexao.close()


def buscar_usuarios_por_nome(nome: str) -> list[dict[str, object]]:
    """Busca usuários cujo nome contenha o texto informado, sem diferenciar maiúsculas/minúsculas."""
    termo = " ".join((nome or "").split())

    if not termo:
        raise ValueError("Informe um nome para realizar a busca.")

    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, nome, telefone, email, ativo, criado_em
                FROM usuarios
                WHERE nome ILIKE %s
                ORDER BY nome, id;
                """,
                (f"%{termo}%",),
            )
            return [dict(registro) for registro in cursor.fetchall()]
    finally:
        conexao.close()


def listar_usuarios(apenas_ativos: bool = True) -> list[dict[str, object]]:
    """Lista os usuários cadastrados, ativos por padrão."""
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            if apenas_ativos:
                cursor.execute(
                    """
                    SELECT id, nome, telefone, email, ativo, criado_em
                    FROM usuarios
                    WHERE ativo = TRUE
                    ORDER BY nome, id;
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT id, nome, telefone, email, ativo, criado_em
                    FROM usuarios
                    ORDER BY nome, id;
                    """
                )

            return [dict(registro) for registro in cursor.fetchall()]
    finally:
        conexao.close()
