-- Dados adicionais da tela de cadastro administrativo.
-- Mantém compatibilidade com contas criadas antes desta migração.

BEGIN;

ALTER TABLE administradores
    ADD COLUMN IF NOT EXISTS sobrenome VARCHAR(100),
    ADD COLUMN IF NOT EXISTS cpf VARCHAR(11),
    ADD COLUMN IF NOT EXISTS data_nascimento DATE,
    ADD COLUMN IF NOT EXISTS whatsapp VARCHAR(20);

CREATE UNIQUE INDEX IF NOT EXISTS uq_administradores_cpf
    ON administradores(cpf)
    WHERE cpf IS NOT NULL;

COMMIT;
