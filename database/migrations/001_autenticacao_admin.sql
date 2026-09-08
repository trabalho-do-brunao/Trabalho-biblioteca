-- Autenticação administrativa do BiblioAvisa.
-- Esta migração é idempotente e pode ser aplicada em bancos já existentes.

BEGIN;

CREATE TABLE IF NOT EXISTS administradores (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(150) NOT NULL,
    email           VARCHAR(150) NOT NULL,
    senha_hash      TEXT NOT NULL,
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_administradores_email_normalizado
    ON administradores (LOWER(email));

CREATE TABLE IF NOT EXISTS sessoes_admin (
    id                  BIGSERIAL PRIMARY KEY,
    administrador_id    INTEGER NOT NULL,
    token_hash          CHAR(64) NOT NULL UNIQUE,
    expira_em           TIMESTAMPTZ NOT NULL,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ultimo_uso_em       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_sessoes_admin_administrador
        FOREIGN KEY (administrador_id)
        REFERENCES administradores(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessoes_admin_administrador
    ON sessoes_admin(administrador_id);

CREATE INDEX IF NOT EXISTS idx_sessoes_admin_expira
    ON sessoes_admin(expira_em);

COMMIT;
