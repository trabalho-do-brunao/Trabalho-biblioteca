"""Testes sem rede nem banco para classificação de falhas."""
import unittest
from app.services.falhas_whatsapp import classificar_falha
from app.services.whatsapp import WhatsAppError

class TestFalhasWhatsApp(unittest.TestCase):
    def test_telefone_invalido(self):
        self.assertEqual(classificar_falha(WhatsAppError('Telefone inválido para envio pelo WhatsApp.'))['codigo'], 'telefone_invalido')

    def test_timeout_nao_autoriza_reenvio(self):
        resultado = classificar_falha(WhatsAppError('O serviço local do WhatsApp excedeu o tempo de resposta.'))
        self.assertEqual(resultado['codigo'], 'timeout')
        self.assertFalse(resultado['reenvio_automatico_permitido'])

    def test_erro_desconhecido_nao_expoe_detalhes(self):
        resultado = classificar_falha(RuntimeError('segredo-interno'))
        self.assertEqual(resultado['codigo'], 'falha_desconhecida')
        self.assertNotIn('segredo-interno', str(resultado))

if __name__ == '__main__':
    unittest.main()
