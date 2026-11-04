"""Valida cenarios/ui-leitura/cenarios.json (lido por 'lab cenarios' via jq): JSON valido, campos
obrigatorios com o tipo certo e 'nome' unico. Sem Protheus.
Uso: python -B lab/tests/test_cenarios_json.py [raiz]   (sai 1 na primeira rodada com erro)
author: daniel.montagna
"""
import json
import sys
from pathlib import Path

RELEASES = {"2610", "2510"}


def texto(v):
    return isinstance(v, str) and v.strip() != ""


def erros_do_cenario(c):
    if not isinstance(c, dict):
        return ["nao e objeto"]
    e = []
    for campo in ("nome", "rotina", "aba"):
        if not texto(c.get(campo)):
            e.append(f"'{campo}' ausente ou vazio")
    mod = c.get("modulo")
    if not isinstance(mod, int) or isinstance(mod, bool) or mod <= 0:
        e.append(f"'modulo' deve ser inteiro positivo (veio {mod!r})")
    menu = c.get("menu")
    if not isinstance(menu, list) or not menu or not all(texto(m) for m in menu):
        e.append("'menu' deve ser lista nao vazia de textos")
    rels = c.get("releases")
    if not isinstance(rels, list) or not all(isinstance(r, str) for r in rels):
        e.append("'releases' deve ser lista de textos")
    elif set(rels) - RELEASES:
        e.append(f"'releases' so aceita {sorted(RELEASES)} (veio {rels})")
    elif len(rels) != len(set(rels)):
        e.append(f"'releases' repetida: {rels}")
    for opcional in ("titulo", "aviso", "help"):
        if opcional in c and not isinstance(c[opcional], str):
            e.append(f"'{opcional}' deve ser texto")
    if "visualizar" in c and not isinstance(c["visualizar"], bool):
        e.append(f"'visualizar' deve ser true/false (veio {c['visualizar']!r})")
    if c.get("visualizar") and c.get("help"):
        e.append("'visualizar' e 'help' nao combinam (o Help substitui o browse)")
    if "parametros" in c and c["parametros"] != "ok":
        e.append(f"'parametros' so aceita \"ok\" (veio {c['parametros']!r})")
    return e


def validar(dados):
    if not isinstance(dados, dict) or not isinstance(dados.get("cenarios"), list) or not dados["cenarios"]:
        return ["raiz deve ter 'cenarios' como lista nao vazia"]
    erros, vistos = [], set()
    for i, c in enumerate(dados["cenarios"]):
        rotulo = c.get("nome", f"#{i}") if isinstance(c, dict) else f"#{i}"
        erros += [f"cenario {rotulo}: {x}" for x in erros_do_cenario(c)]
        if isinstance(c, dict) and texto(c.get("nome")):
            if c["nome"] in vistos:
                erros.append(f"cenario {c['nome']}: 'nome' repetido")
            vistos.add(c["nome"])
    return erros


def autoteste():
    bom = {"nome": "x", "rotina": "MATA010", "modulo": 5, "menu": ["A", "B"], "aba": "X", "releases": ["2610"]}
    assert validar({"cenarios": [bom]}) == [], "autoteste: reprovou cenario correto"
    casos = [dict(bom, modulo="5"), dict(bom, menu=[]), dict(bom, releases=["2410"]), dict(bom, aba=""), dict(bom, parametros="sim"), dict(bom, visualizar="sim"), dict(bom, visualizar=True, help="RECNO"),
             {k: v for k, v in bom.items() if k != "rotina"}]
    for ruim in casos:
        assert validar({"cenarios": [ruim]}), f"autoteste: aprovou cenario invalido {ruim}"
    assert validar({"cenarios": [bom, bom]}), "autoteste: aprovou 'nome' repetido"


def main():
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[2])
    autoteste()
    arq = raiz / "cenarios/ui-leitura/cenarios.json"
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FALHA {arq}: {exc}")
        return 1
    erros = validar(dados)
    for e in erros:
        print(f"FALHA {e}")
    print(f"cenarios: {len(dados.get('cenarios') or [])}  falhas: {len(erros)}")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
