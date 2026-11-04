"""Testes sem Protheus do lab menus / lab menus-diff:
- menus_diff com o dado real de Compras (modulo 2, Atualizacoes, coletado em 03/11/2026);
- menus_diff com arvores sinteticas (grupo novo, item removido, nao comparado);
- mapear_menu contra um menu simulado (pagina falsa), conferindo que so grupos sao clicados.
Rodar:  python -B -m unittest discover -s lab/tests -p 'test_*.py'
author: daniel.montagna
"""
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "tir"))

import mapear_menu as mm
import menus_diff as md

FIX = os.path.join(AQUI, "fixtures", "menus")


def mapa(rel, menus, completo=True):
    return {"release": rel, "modulo": 2, "raizes": ["Atualizações"], "completo": completo, "menus": menus}


class DiffCompras(unittest.TestCase):
    """Dado real: 2610 tem Cadastros (30) e Controle Orcamentario (6); 2510 tem Cadastros (28)."""

    def setUp(self):
        self.a = md.carregar(os.path.join(FIX, "2610", "2.json"))
        self.b = md.carregar(os.path.join(FIX, "2510", "2.json"))
        self.res = md.comparar(self.a, self.b)

    def test_so_na_2610(self):
        self.assertEqual(self.res["so_a"], [("Atualizações", "Controle Orçamentário (6)")])

    def test_so_na_2510(self):
        self.assertEqual(self.res["so_b"], [])

    def test_contagem_diferente(self):
        self.assertEqual(self.res["contagem"], [("Atualizações", "Cadastros", 30, 28)])

    def test_relatorio(self):
        texto, _ = md.relatorio(self.a, self.b, gerado_em="2026-11-04T00:00:00-03:00")
        self.assertIn("# Menu do módulo 2: 2610 × 2510", texto)
        self.assertIn("| Atualizações | Controle Orçamentário (6) |", texto)
        self.assertIn("| Atualizações | Cadastros | 30 | 28 | +2 |", texto)
        self.assertIn("- Itens só na 2510: **0**", texto)
        self.assertIn("**Atenção:**", texto)  # fixtures tem so o primeiro nivel

    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            saida = os.path.join(tmp, "menus-diff-2.md")
            with redirect_stdout(io.StringIO()) as out:
                rc = md.main(["x", os.path.join(FIX, "2610", "2.json"), os.path.join(FIX, "2510", "2.json"), saida])
            self.assertEqual(rc, 0)
            self.assertIn("so 2610=1 so 2510=0 contagem diferente=1", out.getvalue())
            self.assertTrue(os.path.getsize(saida) > 0)
            with redirect_stderr(io.StringIO()):
                self.assertEqual(md.main(["x", os.path.join(tmp, "nao-existe.json"), saida, saida]), 3)
                self.assertEqual(md.main(["x"]), 2)


class DiffSintetico(unittest.TestCase):
    def test_grupo_novo_lista_os_filhos(self):
        a = mapa("2610", {"Atualizações": ["Cadastros (2)", "Novo (2)"],
                          "Atualizações>Cadastros": ["Produtos", "Clientes"],
                          "Atualizações>Novo": ["Rotina X", "Rotina Y"]})
        b = mapa("2510", {"Atualizações": ["Cadastros (2)"],
                          "Atualizações>Cadastros": ["Produtos", "Clientes"]})
        res = md.comparar(a, b)
        self.assertEqual(res["so_a"], [("Atualizações", "Novo (2)"), ("Atualizações>Novo", "Rotina X"),
                                       ("Atualizações>Novo", "Rotina Y")])
        self.assertEqual(res["nao_comparados"], [])

    def test_item_removido_e_caixa(self):
        a = mapa("2610", {"Atualizações": ["CADASTROS (1)"], "Atualizações>Cadastros": ["Produtos"]})
        b = mapa("2510", {"Atualizações": ["Cadastros (2)"], "Atualizações>Cadastros": ["Produtos", "Antiga"]})
        res = md.comparar(a, b)
        self.assertEqual(res["so_a"], [])
        self.assertEqual(res["so_b"], [("Atualizações>Cadastros", "Antiga")])
        self.assertEqual(res["contagem"], [("Atualizações", "CADASTROS", 1, 2)])

    def test_grupo_nao_aberto_de_um_lado(self):
        a = mapa("2610", {"Atualizações": ["Cadastros (1)"], "Atualizações>Cadastros": ["Produtos"]})
        b = mapa("2510", {"Atualizações": ["Cadastros (1)"]}, completo=False)
        res = md.comparar(a, b)
        self.assertEqual(res["so_a"], [])
        self.assertEqual(res["nao_comparados"], [("Atualizações>Cadastros", "2510")])

    def test_duplicados(self):
        a = mapa("2610", {"Atualizações": ["X", "X"]})
        b = mapa("2510", {"Atualizações": ["X"]})
        self.assertEqual(md.comparar(a, b)["so_a"], [("Atualizações", "X")])

    def test_barra_vertical_escapada(self):
        a = mapa("2610", {"Atualizações": ["A|B"]})
        texto, _ = md.relatorio(a, mapa("2510", {"Atualizações": []}), gerado_em="x")
        self.assertIn("A\\|B", texto)


# ---------- menu simulado para o mapear_menu ----------

ARVORE = [("Atualizações", [
    ("Cadastros (2)", [("Produtos", None), ("Fornecedores", None)]),
    ("Pedidos (2)", [("Pedidos de Compra", None), ("Sub (1)", [("Pedidos de Compra", None)])]),
    ("Vazio (0)", []),
]), ("Consultas", [("Cadastros (1)", [("Produtos", None)])])]


class No:
    def __init__(self, caption, filhos):
        self.caption, self.aberto = caption, False
        self.filhos = [No(c, f) for c, f in filhos] if filhos is not None else None


class Elemento:
    def __init__(self, pagina, no):
        self.pagina, self.no = pagina, no

    def click(self):
        self.pagina.cliques.append(self.no.caption)
        if self.no.filhos is None:
            self.pagina.rotinas_abertas.append(self.no.caption)
        elif self.pagina.recolhe or not self.no.aberto:
            self.no.aberto = not self.no.aberto


class Handle:
    def __init__(self, el):
        self.el = el

    def as_element(self):
        return self.el


class PaginaFalsa:
    def __init__(self, recolhe=True):
        self.raiz = [No(c, f) for c, f in ARVORE]
        self.cliques, self.rotinas_abertas, self.recolhe = [], [], recolhe

    def visiveis(self):
        r = []

        def anda(nos):
            for n in nos:
                r.append(n)
                if n.filhos and n.aberto:
                    anda(n.filhos)
        anda(self.raiz)
        return r

    def evaluate(self, js, arg=None):
        assert js is mm.JS_ITENS
        return [n.caption for n in self.visiveis()]

    def evaluate_handle(self, js, arg):
        assert js is mm.JS_ITEM_NA_POSICAO
        i, esperado = arg
        v = self.visiveis()
        return Handle(Elemento(self, v[i]) if i < len(v) and v[i].caption == esperado else None)

    def wait_for_timeout(self, ms):
        pass


class MapeadorSimulado(unittest.TestCase):
    def rodar(self, raizes, profundidade=5, recolhe=True):
        pg = PaginaFalsa(recolhe)
        m = mm.Mapeador(pg, profundidade, 60)
        m.espera_ms = 50
        with redirect_stdout(io.StringIO()):
            for passos in mm.raizes_de(raizes):
                m.mapear_raiz(passos)
        return pg, m

    def esperado_completo(self):
        return {
            "Atualizações": ["Cadastros (2)", "Pedidos (2)", "Vazio (0)"],
            "Atualizações>Cadastros": ["Produtos", "Fornecedores"],
            "Atualizações>Pedidos": ["Pedidos de Compra", "Sub (1)"],
            "Atualizações>Pedidos>Sub": ["Pedidos de Compra"],
            "Consultas": ["Cadastros (1)"],
            "Consultas>Cadastros": ["Produtos"],
        }

    def test_arvore_completa_sem_abrir_rotina(self):
        pg, m = self.rodar("Atualizações,Consultas")
        self.assertEqual(m.menus, self.esperado_completo())
        self.assertEqual(pg.rotinas_abertas, [])
        self.assertTrue(m.completo, m.avisos)
        self.assertEqual([n.caption for n in pg.visiveis()], ["Atualizações", "Consultas"])  # tudo recolhido

    def test_menu_que_nao_recolhe(self):
        pg, m = self.rodar("Atualizações,Consultas", recolhe=False)
        self.assertEqual(m.menus, self.esperado_completo())
        self.assertEqual(pg.rotinas_abertas, [])
        self.assertTrue(any("nao recolheu" in a for a in m.avisos))

    def test_limite_de_profundidade(self):
        _, m = self.rodar("Atualizações", profundidade=1)
        self.assertEqual(list(m.menus), ["Atualizações"])
        self.assertFalse(m.completo)

    def test_subcaminho(self):
        pg, m = self.rodar("Atualizações>Pedidos")
        self.assertEqual(list(m.menus), ["Atualizações>Pedidos", "Atualizações>Pedidos>Sub"])
        self.assertEqual([n.caption for n in pg.visiveis()], ["Atualizações", "Consultas"])

    def test_subcaminho_que_nao_e_grupo(self):
        pg = PaginaFalsa()
        m = mm.Mapeador(pg, 5, 60)
        with redirect_stdout(io.StringIO()), self.assertRaises(AssertionError):
            m.mapear_raiz(["Atualizações", "Cadastros", "Produtos"])
        self.assertEqual(pg.rotinas_abertas, [])

    def test_auxiliares(self):
        self.assertEqual(mm.contagem("Cadastros (30)"), 30)
        self.assertIsNone(mm.contagem("Produtos"))
        self.assertEqual(mm.nome("Central de Ia (1)"), "Central de Ia")
        self.assertEqual(len(mm.raizes_de("todos")), 4)
        self.assertEqual(mm.bloco_inserido(["A", "B (1)", "C"], ["A", "B (1)", "C", "C"], 1), (2, ["C"]))


if __name__ == "__main__":
    unittest.main()
