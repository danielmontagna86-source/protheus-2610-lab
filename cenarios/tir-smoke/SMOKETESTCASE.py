"""Smoke TIR somente leitura do Protheus 2610 Lab: login, abrir rotina padrao, conferir titulo, sair.

Arquitetura de tres arquivos (EngPro tir-test-generator 5.1.0): este TESTCASE, o SMOKETESTSUITE e o
config.json gerado em runtime por "lab tir" (caminho em PLAB_TIR_CONFIG, nunca versionado).
Metodos usados, conferidos na referencia EngPro e no pacote TIR 2.14.12 instalado:
Webapp(config_path), Setup, Program, WaitShow, AssertTrue (sem argumentos), TearDown.
author: daniel.montagna
"""
import os
import unittest

import plab_tir_compat  # noqa: F401  extensao local: selecao do ambiente (ver lab/tir/plab_tir_compat.py)
from tir import Webapp

# Rotina e titulo esperados; sobrescreviveis para outros cenarios de leitura.
MODULO = os.environ.get("PLAB_SMOKE_MODULO", "SIGAFAT")
CODIGO_MODULO = os.environ.get("PLAB_SMOKE_CODIGO_MODULO", "05")
ROTINA = os.environ.get("PLAB_SMOKE_ROTINA", "MATA010")
# Titulo real do browse da MATA010 (observado em 02/11/2026 na 2610): "Atualizacao de Produtos:".
TITULO = os.environ.get("PLAB_SMOKE_TITULO", "Atualizacao de Produtos")


class SMOKETESTCASE(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oHelper = Webapp(config_path=os.environ["PLAB_TIR_CONFIG"])
        cls.oHelper.Setup(MODULO, "", "99", "01", CODIGO_MODULO)
        cls.oHelper.Program(ROTINA)

    def test_titulo_da_rotina(self):
        # Somente leitura: apenas espera o titulo da rotina aparecer; nao inclui nem altera nada.
        self.oHelper.WaitShow(TITULO)
        self.oHelper.AssertTrue()

    @classmethod
    def tearDownClass(cls):
        cls.oHelper.TearDown()


if __name__ == "__main__":
    unittest.main()
