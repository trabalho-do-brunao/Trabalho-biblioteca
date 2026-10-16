-- Migração aditiva: tabela de auditoria sem alterações nas tabelas existentes.
CREATE TABLE IF NOT EXISTS auditoria_eventos (
    id BIGSERIAL PRIMARY KEY,
    acao VARCHAR(80) NOT NULL,
    entidade VARCHAR(60) NOT NULL,
    entidade_id INTEGER NOT NULL CHECK (entidade_id > 0),
    ator_id INTEGER NULL CHECK (ator_id > 0),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auditoria_eventos_data
    ON auditoria_eventos (criado_em DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_auditoria_eventos_entidade
    ON auditoria_eventos (entidade, entidade_id, criado_em DESC);
