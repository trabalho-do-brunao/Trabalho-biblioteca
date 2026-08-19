-- =========================================================
-- Sistema de Gestão de Biblioteca com Integração via WhatsApp
-- Script de criação do banco de dados
--
-- Banco: ecf
-- Usuário: postgres
-- Senha: postgres
-- Porta: 5432
-- =========================================================


-- =========================================================
-- TABELA: usuarios
-- Usuários/leitores cadastrados na biblioteca
-- =========================================================
CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(150) NOT NULL,
    telefone        VARCHAR(20) NOT NULL UNIQUE,   -- número de WhatsApp (ex: 5542999999999)
    email           VARCHAR(150),
    criado_em       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =========================================================
-- TABELA: livros
-- Acervo da biblioteca
-- =========================================================
CREATE TABLE livros (
    id                      SERIAL PRIMARY KEY,
    titulo                  VARCHAR(200) NOT NULL,
    autor                   VARCHAR(150),
    isbn                    VARCHAR(20) UNIQUE,
    quantidade_total        INTEGER NOT NULL DEFAULT 1,
    quantidade_disponivel   INTEGER NOT NULL DEFAULT 1,
    criado_em               TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT quantidade_disponivel_valida
        CHECK (quantidade_disponivel >= 0 AND quantidade_disponivel <= quantidade_total)
);

-- =========================================================
-- TABELA: emprestimos
-- Registro de cada empréstimo realizado
-- =========================================================
CREATE TABLE emprestimos (
    id                          SERIAL PRIMARY KEY,
    usuario_id                  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    livro_id                    INTEGER NOT NULL REFERENCES livros(id) ON DELETE CASCADE,
    data_emprestimo              DATE NOT NULL DEFAULT CURRENT_DATE,
    data_prevista_devolucao      DATE NOT NULL,
    data_devolucao               DATE,             -- preenchido somente quando o livro é devolvido
    status                       VARCHAR(20) NOT NULL DEFAULT 'ativo',
    criado_em                    TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT status_valido
        CHECK (status IN ('ativo', 'devolvido', 'atrasado'))
);

CREATE INDEX idx_emprestimos_status ON emprestimos(status);
CREATE INDEX idx_emprestimos_prazo ON emprestimos(data_prevista_devolucao);

-- =========================================================
-- TABELA: notificacoes
-- Log de mensagens enviadas via WhatsApp
-- =========================================================
CREATE TABLE notificacoes (
    id              SERIAL PRIMARY KEY,
    emprestimo_id   INTEGER NOT NULL REFERENCES emprestimos(id) ON DELETE CASCADE,
    tipo            VARCHAR(20) NOT NULL,   -- 'lembrete' ou 'atraso'
    mensagem        TEXT NOT NULL,
    data_envio      TIMESTAMP NOT NULL DEFAULT NOW(),
    status_envio    VARCHAR(20) NOT NULL DEFAULT 'enviado',
    CONSTRAINT tipo_valido
        CHECK (tipo IN ('lembrete', 'atraso')),
    CONSTRAINT status_envio_valido
        CHECK (status_envio IN ('enviado', 'falha'))
);

CREATE INDEX idx_notificacoes_emprestimo ON notificacoes(emprestimo_id);

-- =========================================================
-- DADOS DE TESTE (opcional - pode remover em produção)
-- =========================================================
INSERT INTO usuarios (nome, telefone, email) VALUES
('Ana Silva', '5542999990001', 'ana.silva@email.com'),
('Bruno Costa', '5542999990002', 'bruno.costa@email.com'),
('Carla Souza', '5542999990003', 'carla.souza@email.com');

INSERT INTO livros (titulo, autor, isbn, quantidade_total, quantidade_disponivel) VALUES
('Dom Casmurro', 'Machado de Assis', '9788525406958', 3, 2),
('1984', 'George Orwell', '9788535914849', 2, 1),
('O Pequeno Príncipe', 'Antoine de Saint-Exupéry', '9788595081512', 4, 4);

INSERT INTO emprestimos (usuario_id, livro_id, data_emprestimo, data_prevista_devolucao, status) VALUES
(1, 1, CURRENT_DATE - INTERVAL '10 days', CURRENT_DATE - INTERVAL '3 days', 'atrasado'),
(2, 2, CURRENT_DATE - INTERVAL '5 days', CURRENT_DATE + INTERVAL '1 day', 'ativo'),
(3, 1, CURRENT_DATE - INTERVAL '2 days', CURRENT_DATE + INTERVAL '5 days', 'ativo');
