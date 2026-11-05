"""Testes sem Protheus do mapear_por_grupo.py (lab menus em modo por grupo, issue #20): as sessoes
sao simuladas e o teste confere quais caminhos viram sessao e como os JSON sao juntados.
Rodar:  python -B -m unittest discover -s lab/tests -p 'test_*.py'
author: daniel.montagna
"""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "tir"))

import mapear_por_grupo as mpg  # noqa: E402

RAIZ = ["Cadastros (2)", "Pedidos (0)", "Liberar de Documentos", "Consultas (1)"]
SUB = {
    "Atualizações>Cadastros": {"Atualizações>Cadastros": ["Produtos", "Fornecedores"]},
    "Atualizações>Consultas": {"Atualizações>Consultas": ["Kardex"]},
}


class MapearPorGrupo(unittest.TestCase):
    def rodar(self, falhar=None, saida_presa=None):
        chamadas = []

        def falsa(rel, modulo, caminho, destino, profundidade, tempo_s):
            chamadas.append((caminho, profundidade))
            if caminho == "Atualizações":
                return 1, {"descricao_modulo": "Compras", "topo": ["Atualizações (3)"], "completo": False,
                           "avisos": ["limite de profundidade (1) atingido; grupos abaixo nao foram abertos"],
                           "menus": {"Atualizações": RAIZ}}
            if caminho == falhar:
                return 1, {"completo": False, "avisos": ["erro: menu nao reagiu"], "menus": {}}
            rc = 4 if caminho == saida_presa else 0
            return rc, {"completo": True, "avisos": [], "menus": SUB[caminho]}

        original = mpg.sessao
        mpg.sessao = falsa
        try:
            with tempfile.TemporaryDirectory() as tmp:
                destino = os.path.join(tmp, "2.json")
                with redirect_stdout(io.StringIO()):
                    rc = mpg.main(["x", "2610", "2", "Atualizações", destino])
                with open(destino, encoding="utf-8") as f:
                    dados = json.load(f)
        finally:
            mpg.sessao = original
        return rc, dados, chamadas

    def test_uma_sessao_por_grupo_com_filhos(self):
        rc, dados, chamadas = self.rodar()
        self.assertEqual(rc, 0)
        # grupo com (0) e rotina solta nao viram sessao; profundidade total preservada (5 - 1)
        self.assertEqual(chamadas, [("Atualizações", 1), ("Atualizações>Cadastros", 4),
                                    ("Atualizações>Consultas", 4)])
        self.assertTrue(dados["completo"])
        self.assertEqual(dados["sessoes"], 3)
        self.assertEqual(dados["descricao_modulo"], "Compras")
        self.assertEqual(set(dados["menus"]), {"Atualizações", "Atualizações>Cadastros", "Atualizações>Consultas"})
        self.assertEqual(dados["avisos"], [])  # o limite de profundidade da 1a sessao e esperado

    def test_grupo_com_erro_deixa_mapa_incompleto(self):
        rc, dados, _ = self.rodar(falhar="Atualizações>Cadastros")
        self.assertEqual(rc, 1)
        self.assertFalse(dados["completo"])
        self.assertIn("erro: menu nao reagiu", dados["avisos"])
        self.assertIn("Atualizações>Consultas", dados["menus"])  # segue para os outros grupos

    def test_grupo_aninhado_com_erro_vira_sessoes_por_subgrupo(self):
        aninhado = {"Atualizações>Cadastros": ["Sub (1)", "Produtos"]}
        sub = {"Atualizações>Cadastros>Sub": ["Item"]}
        chamadas = []

        def falsa(rel, modulo, caminho, destino, profundidade, tempo_s):
            chamadas.append((caminho, profundidade))
            if caminho == "Atualizações":
                return 1, {"completo": False, "avisos": [], "menus": {"Atualizações": ["Cadastros (2)"]}}
            if caminho == "Atualizações>Cadastros":
                return 1, {"completo": False, "avisos": ["erro: Timeout"], "menus": aninhado}
            return 0, {"completo": True, "avisos": [], "menus": sub}

        original = mpg.sessao
        mpg.sessao = falsa
        try:
            with tempfile.TemporaryDirectory() as tmp:
                destino = os.path.join(tmp, "2.json")
                with redirect_stdout(io.StringIO()):
                    rc = mpg.main(["x", "2610", "2", "Atualizações", destino])
                with open(destino, encoding="utf-8") as f:
                    dados = json.load(f)
        finally:
            mpg.sessao = original
        self.assertEqual(rc, 0)
        self.assertEqual(chamadas[-1], ("Atualizações>Cadastros>Sub", 3))
        self.assertTrue(dados["completo"])  # o erro da sessao subdividida nao conta
        self.assertEqual(dados["subdivididos"], ["Atualizações>Cadastros"])
        self.assertEqual(dados["menus"]["Atualizações>Cadastros"], ["Sub (1)", "Produtos"])
        self.assertIn("Atualizações>Cadastros>Sub", dados["menus"])

    def test_saida_nao_confirmada_para_tudo(self):
        rc, dados, chamadas = self.rodar(saida_presa="Atualizações>Cadastros")
        self.assertEqual(rc, 4)
        self.assertNotIn(("Atualizações>Consultas", 4), chamadas)  # nao abre outra sessao com licenca presa
        self.assertFalse(dados["completo"])


if __name__ == "__main__":
    unittest.main()
