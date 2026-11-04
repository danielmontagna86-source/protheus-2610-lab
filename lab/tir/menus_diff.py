"""Compara os mapas de menu (JSON do mapear_menu.py) de duas releases e gera um relatorio Markdown.
Uso:  python menus_diff.py <json_release_a> <json_release_b> <saida.md>
(o lab menus-diff passa a 2610 como A e a 2510 como B). Nao precisa de Protheus nem de Playwright.

O relatorio traz: itens so em A, itens so em B, grupos com contador "(N)" diferente e caminhos que
nao puderam ser comparados (mapeados so de um lado por limite de profundidade/tempo ou raiz diferente).
Itens sao comparados pelo rotulo sem o contador e sem diferenciar caixa.
Codigos de saida: 0 relatorio gerado; 2 uso invalido; 3 JSON ausente ou invalido.
author: daniel.montagna
"""
import datetime
import json
import re
import sys
from collections import Counter

_CONTAGEM = re.compile(r"\s*\((\d+)\)\s*$")
SEP = ">"


def contagem(caption):
    m = _CONTAGEM.search(caption or "")
    return int(m.group(1)) if m else None


def nome(caption):
    return " ".join(_CONTAGEM.sub("", caption or "").split())


def chave(caption):
    return nome(caption).casefold()


def carregar(caminho):
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    if not isinstance(dados, dict) or not isinstance(dados.get("menus"), dict):
        raise ValueError(f"{caminho}: sem o objeto 'menus'")
    return dados


def _normalizar_caminho(caminho):
    return SEP.join(chave(p) for p in caminho.split(SEP))


def _situacao_caminho(caminho, menus_outro):
    """Para um caminho mapeado so de um lado: 'novo' se algum ancestor mapeado do outro lado nao tem
    o grupo (o grupo inteiro e exclusivo) ou 'nao_comparado' (o grupo existe la mas nao foi aberto)."""
    partes = caminho.split(SEP)
    for k in range(len(partes) - 1, 0, -1):
        pai = SEP.join(partes[:k])
        if pai in menus_outro:
            filhos = {chave(c) for c in menus_outro[pai]}
            return "nao_comparado" if partes[k] in filhos else "novo"
    return "nao_comparado"


def comparar(a, b):
    """Devolve dict com so_a, so_b (listas de (caminho, caption)), contagem (lista de
    (caminho, nome, n_a, n_b)) e nao_comparados (lista de (caminho, release))."""
    # indice: caminho normalizado -> (caminho exibido, captions)
    ia = {_normalizar_caminho(k): (k, v) for k, v in a["menus"].items()}
    ib = {_normalizar_caminho(k): (k, v) for k, v in b["menus"].items()}
    menus_a = {k: v[1] for k, v in ia.items()}
    menus_b = {k: v[1] for k, v in ib.items()}
    res = {"so_a": [], "so_b": [], "contagem": [], "nao_comparados": []}

    def exclusivos(origem, destino, rotulo_destino):
        saida = []
        for k, (exibido, itens) in origem.items():
            if k in destino:
                restantes = Counter(chave(c) for c in destino[k])
                for c in itens:
                    if restantes[chave(c)] > 0:
                        restantes[chave(c)] -= 1
                    else:
                        saida.append((exibido, c))
            elif _situacao_caminho(k, destino) == "novo":
                saida.extend((exibido, c) for c in itens)
            else:
                res["nao_comparados"].append((exibido, rotulo_destino))
        return saida

    res["so_a"] = exclusivos(ia, menus_b, b.get("release", "B"))
    res["so_b"] = exclusivos(ib, menus_a, a.get("release", "A"))
    for k, (exibido, itens) in ia.items():
        if k not in menus_b:
            continue
        nb = {}
        for c in menus_b[k]:
            nb.setdefault(chave(c), contagem(c))
        for c in itens:
            n_a, n_b = contagem(c), nb.get(chave(c))
            if n_a is not None and n_b is not None and n_a != n_b:
                res["contagem"].append((exibido, nome(c), n_a, n_b))
    return res


def _cel(texto):
    return str(texto).replace("|", "\\|")


def _caminho_md(caminho):
    return " > ".join(nome(p) for p in caminho.split(SEP))


def relatorio(a, b, gerado_em=None):
    ra, rb = a.get("release", "A"), b.get("release", "B")
    modulo = a.get("modulo", b.get("modulo", "?"))
    descricao = a.get("descricao_modulo") or b.get("descricao_modulo") or ""
    res = comparar(a, b)
    gerado_em = gerado_em or datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    l = [f"# Menu do módulo {modulo}{' — ' + descricao if descricao else ''}: {ra} × {rb}", ""]
    l += [(f"Gerado em {gerado_em} por `lab menus-diff {modulo}` a partir de "
           f"`evidencias/{ra}/menus/{modulo}.json` e `evidencias/{rb}/menus/{modulo}.json`."), ""]
    l += ["| | " + ra + " | " + rb + " |", "|---|---|---|"]
    l += [f"| Coletado em | {a.get('coletado_em', '?')} | {b.get('coletado_em', '?')} |"]
    l += [f"| Raízes | {', '.join(a.get('raizes', []))} | {', '.join(b.get('raizes', []))} |"]
    l += [f"| Profundidade máxima | {a.get('profundidade_max', '?')} | {b.get('profundidade_max', '?')} |"]
    l += [f"| Grupos mapeados | {len(a['menus'])} | {len(b['menus'])} |"]
    l += [f"| Mapa completo | {'sim' if a.get('completo') else 'não'} | {'sim' if b.get('completo') else 'não'} |", ""]
    if not (a.get("completo") and b.get("completo")):
        l += [("> **Atenção:** pelo menos um dos mapas está incompleto (limite de tempo, de profundidade ou "
               "erro): podem faltar diferenças dentro de grupos que não foram abertos. Grupos abertos só "
               "de um lado aparecem em \"Não comparados\"."), ""]
    l += ["## Resumo", "",
          f"- Itens só na {ra}: **{len(res['so_a'])}**",
          f"- Itens só na {rb}: **{len(res['so_b'])}**",
          f"- Grupos com contagem diferente: **{len(res['contagem'])}**", ""]

    def tabela(titulo, linhas):
        out = [f"## {titulo}", ""]
        if not linhas:
            return out + ["Nenhum.", ""]
        out += ["| Caminho | Item |", "|---|---|"]
        out += [f"| {_cel(_caminho_md(c))} | {_cel(i)} |" for c, i in linhas]
        return out + [""]

    l += tabela(f"Só na {ra}", res["so_a"])
    l += tabela(f"Só na {rb}", res["so_b"])
    l += ["## Grupos com contagem diferente", ""]
    if res["contagem"]:
        l += [f"| Caminho | Grupo | {ra} | {rb} | Diferença |", "|---|---|---:|---:|---:|"]
        l += [f"| {_cel(_caminho_md(c))} | {_cel(g)} | {na} | {nb} | {na - nb:+d} |" for c, g, na, nb in res["contagem"]]
    else:
        l += ["Nenhum."]
    l += [""]
    if res["nao_comparados"]:
        l += ["## Não comparados", "", "Caminhos mapeados só de um lado (o outro lado não abriu o grupo).", "",
              "| Caminho | Não mapeado na |", "|---|---|"]
        l += [f"| {_cel(_caminho_md(c))} | {r} |" for c, r in res["nao_comparados"]]
        l += [""]
    avisos = [(ra, x) for x in a.get("avisos", [])] + [(rb, x) for x in b.get("avisos", [])]
    if avisos:
        l += ["## Avisos da coleta", ""] + [f"- {r}: {_cel(x)}" for r, x in avisos] + [""]
    l += ["Coleta somente leitura (`lab menus`): só grupos foram abertos, nenhuma rotina.", ""]
    return "\n".join(l), res


def main(argv):
    if len(argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        a, b = carregar(argv[1]), carregar(argv[2])
    except (OSError, ValueError) as exc:  # json.JSONDecodeError e ValueError
        print(f"menus-diff: {exc}", file=sys.stderr)
        return 3
    texto, res = relatorio(a, b)
    with open(argv[3], "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"menus-diff {a.get('modulo', '?')}: so {a.get('release')}={len(res['so_a'])} "
          f"so {b.get('release')}={len(res['so_b'])} contagem diferente={len(res['contagem'])} "
          f"nao comparados={len(res['nao_comparados'])} relatorio={argv[3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
