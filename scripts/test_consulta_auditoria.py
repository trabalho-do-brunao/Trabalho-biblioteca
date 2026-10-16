"""Testes das validações da consulta de auditoria sem conexão real."""
import unittest
from unittest.mock import patch
from app.repositories.consulta_auditoria import listar_eventos


class TestConsultaAuditoria(unittest.TestCase):
    @patch("app.repositories.consulta_auditoria.conectar")
    def test_limite_invalido_nao_conecta(self, conectar):
        with self.assertRaises(ValueError):
            listar_eventos(limite=101)
        conectar.assert_not_called()

    @patch("app.repositories.consulta_auditoria.conectar")
    def test_deslocamento_negativo_nao_conecta(self, conectar):
        with self.assertRaises(ValueError):
            listar_eventos(deslocamento=-1)
        conectar.assert_not_called()

    @patch("app.repositories.consulta_auditoria.conectar")
    def test_id_invalido_nao_conecta(self, conectar):
        with self.assertRaises(ValueError):
            listar_eventos(entidade_id=0)
        conectar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
