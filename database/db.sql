-- =========================================================
-- BiblioAvisa - Sistema de Gestão de Biblioteca
-- Esquema principal do banco de dados PostgreSQL
-- =========================================================
-- Este arquivo contém somente a estrutura do banco.
-- Dados de demonstração ficam em database/seed.sql.
-- =========================================================

BEGIN;

-- =========================================================
-- TABELA: usuarios
-- Leitores cadastrados na biblioteca.
-- =========================================================
CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(150) NOT NULL,
    telefone        VARCHAR(20) NOT NULL UNIQUE,
    email           VARCHAR(150),
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================
-- TABELA: livros
-- Acervo da biblioteca e dados obtidos pela Google Books API.
-- =========================================================
CREATE TABLE livros (
    id                      SERIAL PRIMARY KEY,
    titulo                  VARCHAR(200) NOT NULL,
    subtitulo               VARCHAR(200),
    autor                   VARCHAR(255),
    isbn                    VARCHAR(20) UNIQUE,
    google_books_id         VARCHAR(100),
    editora                 VARCHAR(150),
    data_publicacao         VARCHAR(20),
    descricao               TEXT,
    numero_paginas          INTEGER,
    url_capa                TEXT,
    quantidade_total        INTEGER NOT NULL DEFAULT 1,
    quantidade_disponivel   INTEGER NOT NULL DEFAULT 1,
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT livros_numero_paginas_valido
        CHECK (numero_paginas IS NULL OR numero_paginas > 0),

    CONSTRAINT livros_quantidade_total_valida
        CHECK (quantidade_total > 0),

    CONSTRAINT livros_quantidade_disponivel_valida
        CHECK (
            quantidade_disponivel >= 0
            AND quantidade_disponivel <= quantidade_total
        )
);

-- =========================================================
-- TABELA: emprestimos
-- Registro da retirada e devolução dos livros.
-- =========================================================
CREATE TABLE emprestimos (
    id                          SERIAL PRIMARY KEY,
    usuario_id                  INTEGER NOT NULL,
    livro_id                    INTEGER NOT NULL,
    data_emprestimo             DATE NOT NULL DEFAULT CURRENT_DATE,
    data_prevista_devolucao     DATE NOT NULL,
    data_devolucao              DATE,
    status                      VARCHAR(20) NOT NULL DEFAULT 'ativo',
    criado_em                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_emprestimos_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_emprestimos_livro
        FOREIGN KEY (livro_id)
        REFERENCES livros(id)
        ON DELETE RESTRICT,

    CONSTRAINT emprestimos_status_valido
        CHECK (status IN ('ativo', 'devolvido', 'atrasado')),

    CONSTRAINT emprestimos_prazo_valido
        CHECK (data_prevista_devolucao >= data_emprestimo),

    CONSTRAINT emprestimos_devolucao_valida
        CHECK (
            data_devolucao IS NULL
            OR data_devolucao >= data_emprestimo
        )
);

-- =========================================================
-- TABELA: renovacoes
-- Histórico das solicitações de renovação de empréstimos.
-- =========================================================
CREATE TABLE renovacoes (
    id                  SERIAL PRIMARY KEY,
    emprestimo_id       INTEGER NOT NULL,
    data_solicitacao    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_anterior       DATE NOT NULL,
    nova_data           DATE,
    status              VARCHAR(20) NOT NULL DEFAULT 'solicitada',
    origem              VARCHAR(20) NOT NULL DEFAULT 'whatsapp',
    motivo_recusa       TEXT,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_renovacoes_emprestimo
        FOREIGN KEY (emprestimo_id)
        REFERENCES emprestimos(id)
        ON DELETE RESTRICT,

    CONSTRAINT renovacoes_status_valido
        CHECK (status IN ('solicitada', 'aprovada', 'recusada')),

    CONSTRAINT renovacoes_origem_valida
        CHECK (origem IN ('whatsapp', 'sistema', 'manual')),

    CONSTRAINT renovacoes_datas_validas
        CHECK (
            (status = 'aprovada' AND nova_data IS NOT NULL AND nova_data > data_anterior)
            OR
            (status IN ('solicitada', 'recusada') AND nova_data IS NULL)
        )
);

-- =========================================================
-- TABELA: mensagens
-- Histórico de mensagens enviadas e recebidas pelo sistema.
-- Substitui a antiga tabela "notificacoes" para também registrar
-- respostas recebidas pelo webhook do WhatsApp.
-- =========================================================
CREATE TABLE mensagens (
    id                      SERIAL PRIMARY KEY,
    usuario_id              INTEGER NOT NULL,
    emprestimo_id           INTEGER,
    direcao                 VARCHAR(10) NOT NULL,
    tipo                    VARCHAR(30) NOT NULL,
    mensagem                TEXT NOT NULL,
    status                  VARCHAR(20) NOT NULL,
    identificador_externo   VARCHAR(255),
    data_referencia         DATE NOT NULL DEFAULT CURRENT_DATE,
    data_mensagem           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_mensagens_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_mensagens_emprestimo
        FOREIGN KEY (emprestimo_id)
        REFERENCES emprestimos(id)
        ON DELETE RESTRICT,

    CONSTRAINT mensagens_direcao_valida
        CHECK (direcao IN ('enviada', 'recebida')),

    CONSTRAINT mensagens_tipo_valido
        CHECK (
            tipo IN (
                'aviso_2_dias',
                'aviso_vencimento',
                'aviso_atraso',
                'solicitacao_renovacao',
                'confirmacao_renovacao',
                'recusa_renovacao',
                'consulta',
                'outro'
            )
        ),

    CONSTRAINT mensagens_status_valido
        CHECK (status IN ('pendente', 'enviado', 'recebido', 'falha'))
);

-- =========================================================
-- ÍNDICES
-- =========================================================
CREATE INDEX idx_usuarios_nome
    ON usuarios(nome);

CREATE INDEX idx_livros_titulo
    ON livros(titulo);

CREATE INDEX idx_emprestimos_usuario
    ON emprestimos(usuario_id);

CREATE INDEX idx_emprestimos_livro
    ON emprestimos(livro_id);

CREATE INDEX idx_emprestimos_status
    ON emprestimos(status);

CREATE INDEX idx_emprestimos_prazo
    ON emprestimos(data_prevista_devolucao);

CREATE INDEX idx_renovacoes_emprestimo
    ON renovacoes(emprestimo_id);

CREATE INDEX idx_mensagens_usuario
    ON mensagens(usuario_id);

CREATE INDEX idx_mensagens_emprestimo
    ON mensagens(emprestimo_id);

CREATE INDEX idx_mensagens_data
    ON mensagens(data_mensagem);

-- Evita registrar duas vezes a mesma mensagem entregue pelo provedor
-- (por exemplo, em reenvios do webhook).
CREATE UNIQUE INDEX uq_mensagens_identificador_externo
    ON mensagens(identificador_externo)
    WHERE identificador_externo IS NOT NULL;

-- Evita que uma rotina automática envie o mesmo tipo de aviso
-- várias vezes para o mesmo empréstimo no mesmo dia.
CREATE UNIQUE INDEX uq_mensagens_aviso_diario
    ON mensagens(emprestimo_id, tipo, data_referencia)
    WHERE direcao = 'enviada'
      AND tipo IN ('aviso_2_dias', 'aviso_vencimento', 'aviso_atraso')
      AND status <> 'falha';

COMMIT;
