"""Mapeia (SOMENTE LEITURA) a arvore de menu de um modulo e grava em JSON. Uso no container lab:
  python mapear_menu.py <release> <modulo> <caminhos> <saida.json>
<caminhos>: "Atualizações" (padrao do lab menus), "Atualizações>Cadastros", lista separada por virgula
("Atualizações,Consultas") ou "todos" (Atualizações, Consultas, Relatórios, Miscelânea).

Como percorre: o menu do SIGAMDI e uma arvore em que clicar num grupo insere os filhos logo abaixo
dele (mesma tecnica do explorar_menu.py: compara os wa-menu-item visiveis antes e depois do clique).
So clica em GRUPOS (caption terminando em "(N)") e nos passos de caminho informados; antes de cada
clique confere, no proprio navegador, que o item na posicao esperada tem o caption esperado. Nenhuma
rotina e aberta. Depois de percorrer um grupo, clica nele de novo para recolher.

Limites (variaveis de ambiente):
  PLAB_MENUS_PROFUNDIDADE  niveis abaixo de cada raiz (padrao 5)
  PLAB_MENUS_TEMPO         segundos de navegacao antes de parar e sair (padrao 1200)
Ao estourar um limite, o JSON e gravado com "completo": false e o script sai com 1.

Sempre sai por Log Off -> Finalizar num finally: sessao presa prende a licenca de desenvolvimento.
Codigos de saida: 0 mapa completo e saida confirmada; 1 mapa incompleto ou erro de navegacao (o JSON
parcial e gravado); 2 uso invalido; 4 saida por Log Off nao confirmada (rode plab restart <rel>).
author: daniel.montagna
"""
import datetime
import json
import os
import re
import sys
import time

RAIZES_TODOS = ["Atualizações", "Consultas", "Relatórios", "Miscelânea"]
_CONTAGEM = re.compile(r"\s*\((\d+)\)\s*$")

# Lista, em ordem de documento, os captions dos wa-menu-item visiveis (mesmo criterio do JS_ITENS
# do explorar_menu.py).
JS_ITENS = """() => { const r=[]; const deep=(root)=>root.querySelectorAll('*').forEach(e=>{
  if(e.tagName.toLowerCase()==='wa-menu-item'){ const b=e.getBoundingClientRect();
    if(b.width>0) r.push((e.getAttribute('caption')||'').replace(/<[^>]+>/g,'').trim()); }
  if(e.shadowRoot) deep(e.shadowRoot)}); deep(document); return r; }"""

# Devolve o wa-menu-item visivel na posicao i SOMENTE se o caption for o esperado (senao null):
# protege contra clicar num item que nao e o grupo pretendido (o que poderia abrir uma rotina).
JS_ITEM_NA_POSICAO = """([i, esperado]) => { const r=[]; const deep=(root)=>root.querySelectorAll('*').forEach(e=>{
  if(e.tagName.toLowerCase()==='wa-menu-item'){ const b=e.getBoundingClientRect(); if(b.width>0) r.push(e); }
  if(e.shadowRoot) deep(e.shadowRoot)}); deep(document);
  const e = r[i]; if(!e) return null;
  return (e.getAttribute('caption')||'').replace(/<[^>]+>/g,'').trim() === esperado ? e : null; }"""


def contagem(caption):
    """'Cadastros (30)' -> 30; item sem contador -> None."""
    m = _CONTAGEM.search(caption or "")
    return int(m.group(1)) if m else None


def nome(caption):
    """Rotulo sem o contador '(N)' e com espacos normalizados: 'Cadastros (30)' -> 'Cadastros'."""
    return " ".join(_CONTAGEM.sub("", caption or "").split())


def eh_grupo(caption):
    return contagem(caption) is not None


def raizes_de(argumento):
    if argumento.strip().lower() == "todos":
        return [[r] for r in RAIZES_TODOS]
    raizes = [[p.strip() for p in c.split(">") if p.strip()] for c in argumento.split(",")]
    return [r for r in raizes if r]


def bloco_inserido(antes, depois, indice):
    """Filhos inseridos ao expandir o item em 'indice': o bloco logo abaixo dele. Devolve
    (inicio, itens) ou None se a mudanca nao for uma insercao logo abaixo do item."""
    n = len(depois) - len(antes)
    if n <= 0:
        return None
    if depois[:indice + 1] == antes[:indice + 1] and depois[indice + 1 + n:] == antes[indice + 1:]:
        return indice + 1, depois[indice + 1:indice + 1 + n]
    return None


class Mapeador:
    def __init__(self, pagina, profundidade, tempo_s):
        self.pg = pagina
        self.profundidade = profundidade
        self.fim = time.time() + tempo_s
        self.menus = {}
        self.avisos = []
        self.completo = True
        self.recolhe = True
        self.espera_ms = 15_000  # tempo maximo para o menu reagir a um clique
        self.clique_js = False  # True na 2510 (ver clicar)

    def itens(self):
        return self.pg.evaluate(JS_ITENS)

    def esperar_mudanca(self, antes, esperado_n=None):
        """Le a lista ate ela mudar e estabilizar (duas leituras iguais seguidas)."""
        fim = time.time() + self.espera_ms / 1000.0
        anterior = None
        while time.time() < fim:
            self.pg.wait_for_timeout(400)
            atual = self.itens()
            pronto = atual != antes and (esperado_n is None or len(atual) - len(antes) == esperado_n)
            if pronto and atual == anterior:
                return atual
            anterior = atual
        return self.itens()

    def clicar(self, indice, caption):
        alvo = self.pg.evaluate_handle(JS_ITEM_NA_POSICAO, [indice, caption]).as_element()
        if alvo is None:
            raise AssertionError(f"item {caption!r} nao esta na posicao {indice} do menu; nada foi clicado")
        if self.clique_js:
            # SmartClient HTML 10 (2510): o click() do Playwright esgotava o tempo depois de um grupo
            # grande aberto ("element is not visible", 03/11/2026); o clique pelo proprio componente
            # mapeou o menu inteiro. O caption ja foi conferido acima: so clica no grupo pretendido.
            alvo.evaluate("e => { e.scrollIntoView({block: 'center'}); e.click(); }")
        else:
            # WebApp 26 (2610): so o clique normal abre o grupo. Limite conhecido: depois de um
            # grupo grande o mapa fica parcial (ver issue no GitHub).
            alvo.click()

    def tempo_esgotado(self):
        if time.time() > self.fim:
            if self.completo:
                self.avisos.append("limite de tempo (PLAB_MENUS_TEMPO) atingido; mapa parcial")
            self.completo = False
            return True
        return False

    def expandir(self, lista, indice, caminho_txt):
        """Clica no item em 'indice' e devolve (lista_nova, inicio, filhos)."""
        caption = lista[indice]
        n = contagem(caption)
        self.clicar(indice, caption)
        depois = self.esperar_mudanca(lista, n)
        bloco = bloco_inserido(lista, depois, indice)
        if bloco is None:
            raise AssertionError(f"'{caminho_txt}': o clique nao inseriu filhos logo abaixo do grupo "
                                 f"({len(lista)} -> {len(depois)} itens visiveis)")
        inicio, filhos = bloco
        if n is not None and len(filhos) != n:
            self.avisos.append(f"'{caminho_txt}': contador ({n}) diferente dos itens encontrados ({len(filhos)})")
        return depois, inicio, filhos

    def recolher(self, lista_expandida, indice, lista_original, caminho_txt):
        """Clica de novo no grupo para recolher. Se a lista nao voltar ao original, so registra:
        a navegacao segue pela lista atual (recalcula as posicoes) e nao tenta recolher de novo."""
        if not self.recolhe:
            return lista_expandida
        self.clicar(indice, lista_expandida[indice])
        atual = self.esperar_mudanca(lista_expandida, len(lista_original) - len(lista_expandida))
        if atual != lista_original:
            self.recolhe = False
            self.avisos.append(f"'{caminho_txt}': grupo nao recolheu com novo clique; os grupos seguintes ficam abertos")
        return atual

    def percorrer(self, lista, indice, caminho, nivel):
        """Expande o grupo em 'indice', registra os filhos, desce nos subgrupos e recolhe.
        Devolve a lista visivel ao final."""
        chave = ">".join(caminho)
        depois, inicio, filhos = self.expandir(lista, indice, chave)
        self.menus[chave] = filhos
        print(f"  {chave}: {len(filhos)} itens", flush=True)
        atual = depois
        pos = inicio
        for filho in filhos:
            if eh_grupo(filho) and contagem(filho) > 0:
                if nivel >= self.profundidade:
                    if self.completo:
                        self.avisos.append(f"limite de profundidade ({self.profundidade}) atingido; grupos abaixo nao foram abertos")
                    self.completo = False
                elif not self.tempo_esgotado():
                    tamanho = len(atual)
                    atual = self.percorrer(atual, pos, caminho + [nome(filho)], nivel + 1)
                    pos += len(atual) - tamanho  # se o subgrupo nao recolheu, os irmaos desceram
            pos += 1
        return self.recolher(atual, indice, lista, chave)

    def localizar(self, lista, rotulo, de=0, ate=None):
        alvo = nome(rotulo).lower()
        for i in range(de, len(lista) if ate is None else ate):
            if nome(lista[i]).lower() == alvo:
                return i
        return None

    def mapear_raiz(self, passos):
        """Abre os passos do caminho (ex.: Atualizações>Cadastros) e percorre o ultimo."""
        lista = self.itens()
        caminho, abertos, indice = [], [], None
        de, ate = 0, None
        for k, passo in enumerate(passos):
            indice = self.localizar(lista, passo, de, ate)
            if indice is None:
                raise AssertionError(f"'{passo}' nao encontrado no menu (caminho {'>'.join(passos)})")
            if k > 0 and not eh_grupo(lista[indice]):
                raise AssertionError(f"'{lista[indice]}' nao e grupo; o mapeamento nao abre rotinas")
            caminho.append(nome(lista[indice]))
            if k == len(passos) - 1:
                break
            antes = lista
            lista, de, filhos = self.expandir(lista, indice, ">".join(caminho))
            abertos.append((antes, indice, ">".join(caminho)))
            ate = de + len(filhos)
        lista = self.percorrer(lista, indice, caminho, 1)
        for antes, i, txt in reversed(abertos):  # recolhe os passos intermediarios
            lista = self.recolher(lista, i, antes, txt)


def main(argv):
    if len(argv) != 5 or not argv[2].isdigit():
        print(__doc__, file=sys.stderr)
        return 2
    rel, modulo, raizes, destino = argv[1], int(argv[2]), raizes_de(argv[3]), argv[4]
    if not raizes:
        print("caminho vazio", file=sys.stderr)
        return 2
    profundidade = int(os.environ.get("PLAB_MENUS_PROFUNDIDADE", "5"))
    tempo_s = int(os.environ.get("PLAB_MENUS_TEMPO", "1200"))

    import plab_pw as pw  # importado aqui para o --help e os testes nao exigirem Playwright

    host, amb = os.environ[f"PLAB_{rel}_HOST"], os.environ[f"PLAB_{rel}_ENV"]
    resultado = {"release": rel, "modulo": modulo, "descricao_modulo": "",
                 "coletado_em": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                 "raizes": [">".join(r) for r in raizes], "profundidade_max": profundidade,
                 "completo": False, "topo": [], "avisos": [], "menus": {}}
    rc = 0
    with pw.navegador() as pg:
        mapa = Mapeador(pg, profundidade, tempo_s)
        mapa.clique_js = rel == "2510"
        try:
            pw.entrar(pg, f"http://{host}:1234/webapp/", amb, os.environ.get("PLAB_ADMIN_USER", "Admin"),
                      pw.senha_admin(rel))
            resultado["descricao_modulo"] = pw.sessao(pg, modulo)
            print("modulo:", resultado["descricao_modulo"], flush=True)
            pw.fechar_avisos(pg)
            pw.fechar_aviso_informativo(pg, "MV_1DUP", 5_000)
            resultado["topo"] = mapa.itens()
            for passos in raizes:
                if mapa.tempo_esgotado():
                    break
                mapa.mapear_raiz(passos)
        except Exception as exc:  # noqa: BLE001  (grava o parcial e sai pelo Log Off mesmo assim)
            mapa.completo = False
            mapa.avisos.append(f"erro: {exc}")
            print("erro:", exc, flush=True)
            try:
                pw.limpar_login(pg)
                pg.screenshot(path=os.path.splitext(destino)[0] + "-erro.png")
            except Exception:  # noqa: BLE001
                pass
        finally:
            resultado.update(completo=mapa.completo, avisos=mapa.avisos, menus=mapa.menus)
            os.makedirs(os.path.dirname(destino) or ".", exist_ok=True)
            with open(destino, "w", encoding="utf-8") as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print("json:", destino, flush=True)
            # Log Off -> Finalizar devolve a licenca de desenvolvimento (fechar o navegador nao).
            try:
                saiu = pw.sair_do_sistema(pg)
            except Exception as exc:  # noqa: BLE001
                print("erro na saida:", exc, flush=True)
                saiu = False
            print("saida:", "ok" if saiu else "FALHOU (plab restart <rel> libera a licenca)", flush=True)
    for aviso in resultado["avisos"]:
        print("aviso:", aviso)
    print(f"grupos mapeados: {len(resultado['menus'])} completo: {'sim' if resultado['completo'] else 'nao'}")
    if not saiu:
        rc = 4
    elif not resultado["completo"]:
        rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
