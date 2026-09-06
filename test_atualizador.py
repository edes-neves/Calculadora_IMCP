import unittest

import atualizador


class TestVersao(unittest.TestCase):
    """Testes de comparação de versões entre a tag da release e o app."""

    def test_extrai_major_menor_patch(self):
        self.assertEqual(atualizador.versao_numerica("v1.2.3"), (1, 2, 3))
        self.assertEqual(atualizador.versao_numerica("1.2.3"), (1, 2, 3))
        self.assertEqual(atualizador.versao_numerica("v2.0.0-beta.1"), (2, 0, 0))

    def test_versao_sem_versao_valida(self):
        self.assertIsNone(atualizador.versao_numerica("sem-verao"))
        self.assertIsNone(atualizador.versao_numerica(""))

    def test_ha_versao_nova(self):
        self.assertTrue(atualizador.ha_versao_nova("v9.0.0"))
        self.assertFalse(atualizador.ha_versao_nova("v1.0.0"))
        self.assertFalse(atualizador.ha_versao_nova(atualizador.VERSAO_ATUAL))

    def test_versao_pulada_guardada(self):
        atualizador.marcar_versao_pulada("v99.0.0")
        self.assertEqual(atualizador.versao_pulada(), "v99.0.0")
        atualizador.marcar_versao_pulada("")


class TestEscolhaDeAsset(unittest.TestCase):
    """Escolha do arquivo da release a ser baixado."""

    def _asset(self, nome):
        return {"name": nome, "browser_download_url": f"https://x/{nome}", "size": 1}

    def test_prefere_appimage(self):
        assets = [self._asset("README.txt"), self._asset("Calculadora_de_IMC_Profissional-x86_64.AppImage")]
        escolhido = atualizador._escolher_asset(assets)
        self.assertTrue(escolhido["name"].endswith(".AppImage"))

    def test_fallback_para_binario(self):
        assets = [self._asset("CalculadoraIMC")]
        self.assertEqual(atualizador._escolher_asset(assets)["name"], "CalculadoraIMC")

    def test_sem_asset_compativel(self):
        assets = [self._asset("screenshot.png")]
        self.assertIsNone(atualizador._escolher_asset(assets))
        self.assertIsNone(atualizador._escolher_asset([]))


if __name__ == "__main__":
    unittest.main()