"""Testes do contrato de estados do WhatsApp, sem banco de dados."""
import unittest
from app.services.status_whatsapp import descrever_status, enriquecer_mensagem

class TestStatusWhatsApp(unittest.TestCase):
    def test_status_conhecidos(self):
        for codigo in ('pendente', 'enviado', 'recebido', 'falha'):
            self.assertEqual(descrever_status(codigo)['codigo'], codigo)

    def test_enviado_nao_comprova_entrega(self):
        self.assertFalse(descrever_status('enviado')['entrega_confirmada'])

    def test_enriquecimento_preserva_original(self):
        original = {'id': 1, 'status': 'falha'}
        resultado = enriquecer_mensagem(original)
        self.assertEqual(original, {'id': 1, 'status': 'falha'})
        self.assertEqual(resultado['status_operacional']['codigo'], 'falha')

if __name__ == '__main__':
    unittest.main()
