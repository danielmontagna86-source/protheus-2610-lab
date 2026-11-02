"""Runner do smoke TIR (ponto de entrada do "lab tir"). author: daniel.montagna"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from SMOKETESTCASE import SMOKETESTCASE  # noqa: E402

if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(SMOKETESTCASE("test_titulo_da_rotina"))
    resultado = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if resultado.wasSuccessful() else 1)
