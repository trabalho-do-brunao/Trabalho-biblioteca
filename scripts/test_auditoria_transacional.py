"""Testa auditoria no cursor da operação, sem banco real."""
import unittest
from unittest.mock import MagicMock
from app.repositories.auditoria import registrar_evento_na_transacao

class TestAuditoriaTransacional(unittest.TestCase):
    def test_registra_sem_commit_proprio(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (19,)
        resultado = registrar_evento_na_transacao(cursor, acao='usuario.criado', entidade='usuario', entidade_id=5)
        self.assertEqual(resultado, 19)
        cursor.execute.assert_called_once()
        self.assertEqual(cursor.execute.call_args.args[1], ('usuario.criado', 'usuario', 5, None))

    def test_rejeita_id_invalido_sem_sql(self):
        cursor = MagicMock()
        with self.assertRaises(ValueError):
            registrar_evento_na_transacao(cursor, acao='usuario.criado', entidade='usuario', entidade_id=0)
        cursor.execute.assert_not_called()

    def test_rejeita_acao_desconhecida(self):
        cursor = MagicMock()
        with self.assertRaises(ValueError):
            registrar_evento_na_transacao(cursor, acao='excluir_tudo', entidade='usuario', entidade_id=1)
        cursor.execute.assert_not_called()

if __name__ == '__main__':
    unittest.main()
