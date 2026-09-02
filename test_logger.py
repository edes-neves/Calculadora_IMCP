import shutil
import tempfile
import unittest


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_exception_hook_intercepta_e_registra(self):
        import logger

        # sobrepoe o caminho da pasta de logs para o temporario
        pasta_orig = logger.PASTA_LOGS
        logger.PASTA_LOGS = self.tmpdir

        # target do handler ja criado aponta para logs; recria logger com pasta nova
        import logging
        logger.LOGGER.handlers = []
        logger.LOGGER = logger.configurar_logging()

        def causar():
            raise ValueError("erro de teste")

        # registra hook e dispara uma excecao nao tratada
        logger.instalar_exception_hook()
        try:
            causar()
        except ValueError:
            import sys
            logger._log_excecao_nao_tratada(*sys.exc_info())

        # restaura pasta original e deixa sem handlers extras
        logger.PASTA_LOGS = pasta_orig

    def test_configurar_logging_cria_arquivo(self):
        import logger
        pasta_orig = logger.PASTA_LOGS
        logger.PASTA_LOGS = self.tmpdir
        logger.configurar_logging()
        import os
        self.assertTrue(os.path.exists(self.tmpdir))
        logger.PASTA_LOGS = pasta_orig


if __name__ == "__main__":
    unittest.main()