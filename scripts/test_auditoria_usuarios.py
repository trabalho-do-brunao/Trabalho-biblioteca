"""Garante que operações de usuários e auditoria compartilhem uma transação."""
import unittest
from unittest.mock import MagicMock, patch
from app.repositories.usuarios import cadastrar_usuario, atualizar_usuario, definir_usuario_ativo

class TestAuditoriaUsuarios(unittest.TestCase):
    def setUp(self):
        self.conexao = MagicMock()
        self.cursor = MagicMock()
        self.conexao.cursor.return_value.__enter__.return_value = self.cursor
        self.patcher = patch("app.repositories.usuarios.conectar", return_value=self.conexao)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_cadastro_registra_auditoria_antes_do_commit(self):
        self.cursor.fetchone.side_effect = [{"id": 7, "nome": "Ana"}, (21,)]
        usuario = cadastrar_usuario("Ana", "11987654321")
        self.assertEqual(usuario["id"], 7)
        self.assertEqual(self.cursor.execute.call_count, 2)
        self.assertIn("auditoria_eventos", self.cursor.execute.call_args_list[1].args[0])
        self.conexao.commit.assert_called_once()

    def test_atualizacao_sem_registro_nao_audita(self):
        self.cursor.fetchone.return_value = None
        self.assertIsNone(atualizar_usuario(99, "Ana", "11987654321"))
        self.assertEqual(self.cursor.execute.call_count, 1)

    def test_status_registra_auditoria(self):
        self.cursor.fetchone.side_effect = [{"id": 7, "ativo": False}, (22,)]
        definir_usuario_ativo(7, False)
        self.assertEqual(self.cursor.execute.call_count, 2)
        self.assertEqual(self.cursor.execute.call_args_list[1].args[1][0], "usuario.status_alterado")

    def test_falha_na_auditoria_impede_commit(self):
        self.cursor.fetchone.side_effect = [{"id": 7}, RuntimeError("erro auditoria")]
        with self.assertRaises(RuntimeError):
            cadastrar_usuario("Ana", "11987654321")
        self.conexao.commit.assert_not_called()
        self.conexao.close.assert_called_once()

if __name__ == "__main__":
    unittest.main()
