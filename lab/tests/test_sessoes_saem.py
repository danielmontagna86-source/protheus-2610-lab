"""Todo script Python de lab/tir/ e cenarios/ que abre sessao no Protheus pelo plab_pw (chama
entrar, ou login_po_ui direto como o instalar_procedures.py) tambem precisa chamar sair_do_sistema (Log Off -> Finalizar). Fechar o navegador nao
devolve a licenca de desenvolvimento: em 03/11/2026 o lab/tir/explorar_menu.py nao saia e
prendia a licenca ate 'plab restart <rel>'.

Analise estatica (ast): so conta chamada de verdade (pw.entrar(...), entrar(...)); comentario ou
texto citando o nome nao conta. plab_pw.py e a biblioteca (define as funcoes) e fica de fora.
Uso: python -B lab/tests/test_sessoes_saem.py [raiz]   (sai 1 se algum script nao sai)
author: daniel.montagna
"""
import ast
import sys
from pathlib import Path

PASTAS = ("lab/tir", "cenarios")
BIBLIOTECA = "plab_pw.py"
ABRE = ("entrar", "login_po_ui")
FECHA = "sair_do_sistema"


def chamadas(fonte):
    """Nomes de funcao chamados no fonte: f(...) -> 'f', modulo.f(...) -> 'f'."""
    nomes = set()
    for no in ast.walk(ast.parse(fonte)):
        if isinstance(no, ast.Call):
            if isinstance(no.func, ast.Name):
                nomes.add(no.func.id)
            elif isinstance(no.func, ast.Attribute):
                nomes.add(no.func.attr)
    return nomes


def problema(fonte):
    """None se o fonte esta ok; senao, a descricao da falha."""
    nomes = chamadas(fonte)
    abre = sorted(n for n in ABRE if n in nomes)
    if abre and FECHA not in nomes:
        return f"chama {', '.join(abre)}() e nao chama {FECHA}() (prende licenca de desenvolvimento)"
    return None


def autoteste():
    """Garante que o detector reprova o caso ruim e aprova os bons (evita teste que sempre passa)."""
    ruim = "import plab_pw as pw\n# pw.sair_do_sistema(pg) so em comentario\npw.entrar(pg, u, a, x, s)\n"
    bons = [
        "import plab_pw as pw\npw.entrar(pg, u, a, x, s)\npw.sair_do_sistema(pg)\n",
        "from plab_pw import entrar, sair_do_sistema\nentrar(pg, u, a, x, s)\nsair_do_sistema(pg)\n",
        "import plab_pw as pw\npw.login_po_ui(pg, x, s)\npw.sair_do_sistema(pg, timeout_ms=1)\n",
        "import plab_pw as pw\nprint('sem sessao')\n",
    ]
    assert problema(ruim), "autoteste: detector aprovou script que nao sai"
    assert problema("import plab_pw as pw\npw.login_po_ui(pg, x, s)\n"), "autoteste: login_po_ui sem saida passou"
    for b in bons:
        assert problema(b) is None, f"autoteste: detector reprovou script correto:\n{b}"


def main():
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[2])
    autoteste()
    falhas = total = 0
    for pasta in PASTAS:
        for arq in sorted((raiz / pasta).rglob("*.py")):
            if arq.name == BIBLIOTECA:
                continue
            rel = arq.relative_to(raiz)
            erro = problema(arq.read_text(encoding="utf-8"))
            if erro:
                falhas += 1
                print(f"FALHA {rel}: {erro}")
            elif set(ABRE) & chamadas(arq.read_text(encoding="utf-8")):
                total += 1
                print(f"ok   {rel}")
    print(f"scripts com sessao: {total + falhas}  falhas: {falhas}")
    if total + falhas == 0:
        print("FALHA nenhum script com sessao encontrado (caminhos mudaram?)")
        return 1
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
