"""Validação do contrato de auditoria sem gravar no banco."""
import unittest
from unittest.mock import patch
from app.repositories.auditoria import registrar_evento

class TestAuditoriaContrato(unittest.TestCase):
    @patch('app.repositories.auditoria.conectar')
    def test_rejeita_acao_desconhecida_sem_abrir_conexao(self, conectar):
        with self.assertRaises(ValueError):
            registrar_evento(acao='invalida', entidade='usuario', entidade_id=1)
        conectar.assert_not_called()

    @patch('app.repositories.auditoria.conectar')
    def test_rejeita_id_invalido_sem_abrir_conexao(self, conectar):
        with self.assertRaises(ValueError):
            registrar_evento(acao='usuario.criado', entidade='usuario', entidade_id=0)
        conectar.assert_not_called()

if __name__ == '__main__':
    unittest.main()
