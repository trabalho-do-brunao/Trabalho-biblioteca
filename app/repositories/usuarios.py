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

    Números brasileiros informados apenas com DDD + número recebem o código 55.
    Quando o usuário informa explicitamente ``+`` ou ``00`` no início, o código
    internacional é preservado e não é reinterpretado como número brasileiro.
    """
    entrada = (telefone or "").strip()
    internacional_explicito = entrada.startswith("+") or entrada.startswith("00")
    digitos = re.sub(r"\D", "", entrada)

    if entrada.startswith("00"):
        digitos = digitos[2:]

    if not internacional_explicito and len(digitos) in (10, 11):
        digitos = "55" + digitos

    tamanho_minimo = 8 if internacional_explicito else 12
    if not tamanho_minimo <= len(digitos) <= 15:
        raise ValueError(
            "Telefone inválido. Para números brasileiros, informe DDD e número. "
            "Para números internacionais, informe o código do país com + ou 00."
        )

    return digitos


def _candidatos_telefone_busca(telefone: str) -> list[str]:
    """Gera formas equivalentes úteis para identificar números brasileiros."""
    normalizado = normalizar_telefone(telefone)
    candidatos = [normalizado]

    if not normalizado.startswith("55"):
        return candidatos

    if len(normalizado) == 13 and normalizado[4] == "9":
        candidatos.append(normalizado[:4] + normalizado[5:])
    elif len(normalizado) == 12 and normalizado[4] in {"6", "7", "8", "9"}:
        candidatos.append(normalizado[:4] + "9" + normalizado[4:])

    return list(dict.fromkeys(candidatos))


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


def atualizar_usuario(
    usuario_id: int,
    nome: str,
    telefone: str,
    email: str | None = None,
) -> dict[str, object] | None:
    """Atualiza os dados editáveis de um usuário e retorna o registro atualizado."""
    if not isinstance(usuario_id, int) or usuario_id <= 0:
        raise ValueError("O ID do usuário deve ser um número inteiro positivo.")

    nome_limpo = validar_nome(nome)
    telefone_normalizado = normalizar_telefone(telefone)
    email_normalizado = normalizar_email(email)
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                UPDATE usuarios
                SET nome = %s,
                    telefone = %s,
                    email = %s
                WHERE id = %s
                RETURNING id, nome, telefone, email, ativo, criado_em;
                """,
                (nome_limpo, telefone_normalizado, email_normalizado, usuario_id),
            )
            registro = cursor.fetchone()

        conexao.commit()
        return dict(registro) if registro else None

    except UniqueViolation as erro:
        conexao.rollback()
        raise UsuarioDuplicadoError(
            "Já existe um usuário cadastrado com este telefone."
        ) from erro
    except psycopg2.Error as erro:
        conexao.rollback()
        raise RuntimeError("Não foi possível atualizar o usuário.") from erro
    finally:
        conexao.close()


def definir_usuario_ativo(usuario_id: int, ativo: bool) -> dict[str, object] | None:
    """Ativa ou inativa um usuário sem apagar seu histórico."""
    if not isinstance(usuario_id, int) or usuario_id <= 0:
        raise ValueError("O ID do usuário deve ser um número inteiro positivo.")

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                UPDATE usuarios
                SET ativo = %s
                WHERE id = %s
                RETURNING id, nome, telefone, email, ativo, criado_em;
                """,
                (bool(ativo), usuario_id),
            )
            registro = cursor.fetchone()
        conexao.commit()
        return dict(registro) if registro else None
    except psycopg2.Error as erro:
        conexao.rollback()
        raise RuntimeError("Não foi possível alterar a situação do usuário.") from erro
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
    """Busca usuário pelo telefone, incluindo variação canônica brasileira do WhatsApp."""
    candidatos = _candidatos_telefone_busca(telefone)
    telefone_exato = candidatos[0]
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, nome, telefone, email, ativo, criado_em
                FROM usuarios
                WHERE telefone = ANY(%s)
                ORDER BY CASE WHEN telefone = %s THEN 0 ELSE 1 END, id
                LIMIT 1;
                """,
                (candidatos, telefone_exato),
            )
            registro = cursor.fetchone()
            return dict(registro) if registro else None
    finally:
        conexao.close()


def buscar_usuarios_por_nome(nome: str) -> list[dict[str, object]]:
    """Busca usuários cujo nome contenha o texto informado."""
    termo = " ".join((nome or "").split())
    if not termo:
        raise ValueError("Informe um nome para realizar a busca.")
    return buscar_usuarios(termo, incluir_inativos=True)


def buscar_usuarios(termo: str, incluir_inativos: bool = True) -> list[dict[str, object]]:
    """Pesquisa por ID, nome, telefone ou e-mail."""
    termo_limpo = " ".join((termo or "").split())
    if not termo_limpo:
        return listar_usuarios(apenas_ativos=not incluir_inativos)

    digitos = re.sub(r"\D", "", termo_limpo)
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, nome, telefone, email, ativo, criado_em
                FROM usuarios
                WHERE (%s OR ativo = TRUE)
                  AND (
                    CAST(id AS TEXT) = %s
                    OR nome ILIKE %s
                    OR COALESCE(email, '') ILIKE %s
                    OR (%s <> '' AND telefone LIKE %s)
                  )
                ORDER BY nome, id;
                """,
                (
                    incluir_inativos,
                    termo_limpo,
                    f"%{termo_limpo}%",
                    f"%{termo_limpo}%",
                    digitos,
                    f"%{digitos}%",
                ),
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
