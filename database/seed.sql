-- =========================================================
-- BiblioAvisa - Dados de demonstração
-- Execute este arquivo somente depois de database/db.sql.
-- =========================================================

BEGIN;

INSERT INTO usuarios (nome, telefone, email)
VALUES
    ('Ana Silva', '5542999990001', 'ana.silva@email.com'),
    ('Bruno Costa', '5542999990002', 'bruno.costa@email.com'),
    ('Carla Souza', '5542999990003', 'carla.souza@email.com')
ON CONFLICT (telefone) DO NOTHING;

INSERT INTO livros (
    titulo,
    autor,
    isbn,
    editora,
    data_publicacao,
    numero_paginas,
    quantidade_total,
    quantidade_disponivel
)
VALUES
    ('Dom Casmurro', 'Machado de Assis', '9788525406958', NULL, NULL, NULL, 3, 2),
    ('1984', 'George Orwell', '9788535914849', NULL, NULL, NULL, 2, 1),
    ('O Pequeno Príncipe', 'Antoine de Saint-Exupéry', '9788595081512', NULL, NULL, NULL, 4, 4)
ON CONFLICT (isbn) DO NOTHING;

-- Empréstimo atrasado de Ana.
INSERT INTO emprestimos (
    usuario_id,
    livro_id,
    data_emprestimo,
    data_prevista_devolucao,
    status
)
SELECT
    u.id,
    l.id,
    CURRENT_DATE - 10,
    CURRENT_DATE - 3,
    'atrasado'
FROM usuarios u
JOIN livros l ON l.isbn = '9788525406958'
WHERE u.telefone = '5542999990001'
  AND NOT EXISTS (
      SELECT 1
      FROM emprestimos e
      WHERE e.usuario_id = u.id
        AND e.livro_id = l.id
        AND e.data_emprestimo = CURRENT_DATE - 10
  );

-- Empréstimo que vence amanhã, usado para testes da automação.
INSERT INTO emprestimos (
    usuario_id,
    livro_id,
    data_emprestimo,
    data_prevista_devolucao,
    status
)
SELECT
    u.id,
    l.id,
    CURRENT_DATE - 5,
    CURRENT_DATE + 1,
    'ativo'
FROM usuarios u
JOIN livros l ON l.isbn = '9788535914849'
WHERE u.telefone = '5542999990002'
  AND NOT EXISTS (
      SELECT 1
      FROM emprestimos e
      WHERE e.usuario_id = u.id
        AND e.livro_id = l.id
        AND e.data_emprestimo = CURRENT_DATE - 5
  );

-- Empréstimo em dia.
INSERT INTO emprestimos (
    usuario_id,
    livro_id,
    data_emprestimo,
    data_prevista_devolucao,
    status
)
SELECT
    u.id,
    l.id,
    CURRENT_DATE - 2,
    CURRENT_DATE + 5,
    'ativo'
FROM usuarios u
JOIN livros l ON l.isbn = '9788525406958'
WHERE u.telefone = '5542999990003'
  AND NOT EXISTS (
      SELECT 1
      FROM emprestimos e
      WHERE e.usuario_id = u.id
        AND e.livro_id = l.id
        AND e.data_emprestimo = CURRENT_DATE - 2
  );

COMMIT;
