"""Valida cenarios/ui-gravacao/gravacoes.json (lido por 'lab gravacoes' via jq e pelo
gravacao_ui.py): JSON valido, campos obrigatorios com o tipo certo, 'nome' unico e chave de teste
que nao se confunde com dado da base (prefixo ZZ, ou numero lido do formulario). Sem Protheus.
Uso: python -B lab/tests/test_gravacoes_json.py [raiz]   (sai 1 se houver erro)
author: daniel.montagna
"""
import json
import sys
from pathlib import Path

RELEASES = {"2610", "2510"}
OPCIONAIS_TEXTO = ("aviso", "titulo", "botao", "botao_excluir", "form_incluir", "campo_reabre", "tabela")


def texto(v):
    return isinstance(v, str) and v.strip() != ""


def erros_do_cenario(c):
    if not isinstance(c, dict):
        return ["nao e objeto"]
    e = []
    for campo in ("nome", "rotina"):
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
    elif set(rels) - RELEASES or len(rels) != len(set(rels)):
        e.append(f"'releases' so aceita {sorted(RELEASES)} sem repetir (veio {rels})")
    # Chave do registro de teste: fixa com prefixo ZZ (nao colide com a base) ou lida do formulario.
    if texto(c.get("chave")) == texto(c.get("chave_campo")):
        e.append("informe exatamente um de 'chave' ou 'chave_campo'")
    elif texto(c.get("chave")) and not c["chave"].upper().startswith("ZZ"):
        e.append(f"'chave' deve comecar com ZZ (veio {c['chave']!r})")
    for opcional in OPCIONAIS_TEXTO:
        if opcional in c and not texto(c[opcional]):
            e.append(f"'{opcional}' deve ser texto nao vazio")
    for opcional in ("pesquisa",):
        if opcional in c and not isinstance(c[opcional], bool):
            e.append(f"'{opcional}' deve ser true/false")
    if "parametros" in c and c["parametros"] != "ok":
        e.append(f"'parametros' so aceita \"ok\" (veio {c['parametros']!r})")
    campos = c.get("campos")
    if not isinstance(campos, list) or not campos:
        e.append("'campos' deve ser lista nao vazia (o 1o e esperado ao abrir o formulario)")
    else:
        for k, f in enumerate(campos):
            if not isinstance(f, dict) or not texto(f.get("campo")):
                e.append(f"campos[{k}]: 'campo' ausente")
            elif "valor" in f and "opcao" in f:
                e.append(f"campos[{k}]: use 'valor' ou 'opcao', nao os dois")
    for k, item in enumerate(c.get("itens", [])):
        if not isinstance(item, dict) or not texto(item.get("coluna")) or not texto(item.get("valor")):
            e.append(f"itens[{k}]: 'coluna' e 'valor' obrigatorios")
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
    bom = {"nome": "x", "rotina": "FINA010", "modulo": 6, "menu": ["A", "B"], "chave": "ZZLAB01",
           "campos": [{"campo": "M->ED_CODIGO", "valor": "ZZLAB01"}], "releases": ["2610"]}
    assert validar({"cenarios": [bom]}) == [], "autoteste: reprovou cenario correto"
    num = dict({k: v for k, v in bom.items() if k != "chave"}, chave_campo="cA110Num",
               itens=[{"coluna": "Produto", "valor": "IND.001"}])
    assert validar({"cenarios": [num]}) == [], "autoteste: reprovou cenario com chave_campo"
    casos = [dict(bom, chave="LAB01"), dict(bom, chave_campo="cNum"), {k: v for k, v in bom.items() if k != "chave"},
             dict(bom, campos=[]), dict(bom, campos=[{"campo": "A", "valor": "1", "opcao": "x"}]),
             dict(bom, modulo="6"), dict(bom, releases=["2410"]), dict(bom, pesquisa="nao"),
             dict(bom, itens=[{"coluna": "Produto"}]), dict(bom, botao="")]
    for ruim in casos:
        assert validar({"cenarios": [ruim]}), f"autoteste: aprovou cenario invalido {ruim}"
    assert validar({"cenarios": [bom, bom]}), "autoteste: aprovou 'nome' repetido"


def main():
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[2])
    autoteste()
    arq = raiz / "cenarios/ui-gravacao/gravacoes.json"
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FALHA {arq}: {exc}")
        return 1
    erros = validar(dados)
    for e in erros:
        print(f"FALHA {e}")
    print(f"gravacoes: {len(dados.get('cenarios') or [])}  falhas: {len(erros)}")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
