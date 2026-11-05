"""Mapeia (SOMENTE LEITURA) o menu de um modulo grupo a grupo, uma sessao por grupo, e junta tudo
num JSON no mesmo formato do mapear_menu.py. Uso no container lab:
  python mapear_por_grupo.py <release> <modulo> <caminhos> <saida.json>

Por que: no WebApp 26 (2610) um grupo grande aberto nao recolhe com novo clique e o proximo grupo
fica fora da area visivel; o mapa numa sessao so parava em 2 grupos (issue #20). Aqui cada sessao
abre so <raiz>><grupo>, mapeia a subarvore e sai por Log Off -> Finalizar (mapear_menu.py).

1a sessao: lista os filhos de cada raiz (profundidade 1). Depois, uma sessao por filho que e grupo,
com profundidade PLAB_MENUS_PROFUNDIDADE - 1 (a mesma profundidade total do modo normal). Se a
sessao de um grupo falhar com erro e ele tiver subgrupos, cada subgrupo vira uma sessao propria
(lista em "subdivididos" no JSON).
Para na primeira sessao cuja saida por Log Off nao foi confirmada (licenca presa): codigo 4.
Codigos de saida iguais aos do mapear_menu.py.
author: daniel.montagna
"""
import datetime
import json
import os
import subprocess
import sys

import mapear_menu as mm

AQUI = os.path.dirname(os.path.abspath(__file__))


def sessao(rel, modulo, caminho, destino, profundidade, tempo_s):
    """Roda o mapear_menu.py numa sessao propria; devolve (rc, json ou None)."""
    env = dict(os.environ, PLAB_MENUS_PROFUNDIDADE=str(profundidade), PLAB_MENUS_TEMPO=str(tempo_s))
    print(f"-- sessao: {caminho} (profundidade {profundidade})", flush=True)
    try:
        rc = subprocess.run([sys.executable, "-u", os.path.join(AQUI, "mapear_menu.py"), rel, str(modulo),
                             caminho, destino], env=env, timeout=tempo_s + 300, check=False).returncode
    except subprocess.TimeoutExpired:
        print(f"   cortada pelo tempo; a sessao pode ter ficado presa: plab restart {rel}", flush=True)
        return 124, None
    dados = None
    if os.path.exists(destino):
        with open(destino, encoding="utf-8") as f:
            dados = json.load(f)
    return rc, dados


def main(argv):
    if len(argv) != 5 or not argv[2].isdigit():
        print(__doc__, file=sys.stderr)
        return 2
    rel, modulo, destino = argv[1], int(argv[2]), argv[4]
    raizes = [">".join(r) for r in mm.raizes_de(argv[3])]
    if not raizes:
        print("caminho vazio", file=sys.stderr)
        return 2
    profundidade = int(os.environ.get("PLAB_MENUS_PROFUNDIDADE", "5"))
    tempo_s = int(os.environ.get("PLAB_MENUS_TEMPO", "1200"))
    temp = os.path.splitext(destino)[0] + ".partes"
    os.makedirs(temp, exist_ok=True)

    resultado = {"release": rel, "modulo": modulo, "descricao_modulo": "",
                 "coletado_em": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                 "raizes": raizes, "profundidade_max": profundidade, "completo": True, "topo": [],
                 "avisos": [], "menus": {}, "sessoes": 0, "modo": "por grupo", "subdivididos": []}
    rc_final = 0

    def juntar(dados, ignorar_profundidade):
        resultado["menus"].update(dados.get("menus", {}))
        resultado["topo"] = resultado["topo"] or dados.get("topo", [])
        resultado["descricao_modulo"] = resultado["descricao_modulo"] or dados.get("descricao_modulo", "")
        for aviso in dados.get("avisos", []):
            if ignorar_profundidade and aviso.startswith("limite de profundidade"):
                continue
            resultado["avisos"].append(aviso)
            if not aviso.startswith("'"):  # erro, tempo ou profundidade: o mapa ficou parcial
                resultado["completo"] = False

    def mapear_grupo(caminho, prof, rotulo):
        """Uma sessao para o grupo; se ela falhar com erro e o grupo tiver subgrupos, refaz cada
        subgrupo numa sessao propria (no WebApp 26 o problema se repete em grupos aninhados)."""
        rc, dados = sessao(rel, modulo, caminho, os.path.join(temp, f"{rotulo}.json"), prof, tempo_s)
        resultado["sessoes"] += 1
        if rc in (4, 124):
            if dados:
                juntar(dados, ignorar_profundidade=False)
            resultado["completo"] = False
            return rc
        if not dados:
            resultado["completo"] = False
            resultado["avisos"].append(f"'{caminho}': sessao sem resultado (rc={rc})")
            return rc
        filhos = dados.get("menus", {}).get(caminho)
        subgrupos = [f for f in (filhos or []) if mm.eh_grupo(f) and mm.contagem(f) > 0]
        if dados.get("completo") or prof <= 1 or not subgrupos:
            juntar(dados, ignorar_profundidade=False)
            if not dados.get("completo"):
                resultado["completo"] = False
            return rc
        # falhou no meio: fica so a lista do proprio grupo e cada subgrupo vira uma sessao
        print(f"   '{caminho}' incompleto; subdividindo em {len(subgrupos)} sessoes", flush=True)
        resultado["menus"][caminho] = filhos
        resultado["subdivididos"].append(caminho)
        for k, filho in enumerate(subgrupos):
            rc = mapear_grupo(f"{caminho}>{mm.nome(filho)}", prof - 1, f"{rotulo}-{k}")
            if rc in (4, 124):
                return rc
        return 0

    for n, raiz in enumerate(raizes):
        rc, dados = sessao(rel, modulo, raiz, os.path.join(temp, f"raiz{n}.json"), 1, tempo_s)
        resultado["sessoes"] += 1
        if dados:
            juntar(dados, ignorar_profundidade=True)
        if rc == 4 or rc == 124:
            resultado["completo"] = False
            rc_final = rc
            break
        filhos = (dados or {}).get("menus", {}).get(raiz)
        if filhos is None:
            resultado["completo"] = False
            resultado["avisos"].append(f"'{raiz}': nao listado; grupos nao mapeados")
            continue
        for k, filho in enumerate(filhos):
            if not mm.eh_grupo(filho) or mm.contagem(filho) == 0:
                continue
            rc = mapear_grupo(f"{raiz}>{mm.nome(filho)}", max(profundidade - 1, 1), f"raiz{n}-g{k}")
            if rc in (4, 124):
                rc_final = rc
                break
        if rc_final:
            break

    with open(destino, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
        f.write("\n")
    for aviso in resultado["avisos"]:
        print("aviso:", aviso)
    print(f"json: {destino}")
    print(f"sessoes: {resultado['sessoes']} grupos mapeados: {len(resultado['menus'])} "
          f"completo: {'sim' if resultado['completo'] else 'nao'}")
    if rc_final:
        return rc_final
    return 0 if resultado["completo"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
