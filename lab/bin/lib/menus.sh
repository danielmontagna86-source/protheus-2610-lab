#!/usr/bin/env bash
# lab menus <release> <modulo> [caminho] - mapeia, SOMENTE LEITURA, a arvore de menu do modulo e grava
# evidencias/<release>/menus/<modulo>.json. So abre grupos ("Nome (N)"), nunca rotinas, e sai por
# Log Off -> Finalizar (lab/tir/mapear_menu.py). Caminho padrao "Atualizações"; aceita
# "Atualizações>Cadastros", lista separada por virgula ou "todos".
# Limites: PLAB_MENUS_PROFUNDIDADE (5), PLAB_MENUS_TEMPO (1200 s de navegacao) e PLAB_MENUS_LIMITE
# (corte duro do processo, padrao TEMPO+300 s; se ele cortar, a sessao fica presa: plab restart <rel>).
# Saida: 0 mapa completo; 1 mapa incompleto/erro (JSON parcial gravado); 2 uso invalido;
#        4 saida por Log Off nao confirmada; 124 corte duro por tempo.
set -uo pipefail
. "${PLAB_HOME:-/opt/plab}/lab/bin/lib/comum.sh"

rel=${1:-}; modulo=${2:-}; caminho=${3:-Atualizações}
validar_release "$rel" || exit 2
case "$modulo" in
  ''|*[!0-9]*) erro "modulo invalido: '$modulo' (use o codigo numerico, ex.: 2 = Compras)"; exit 2 ;;
esac
modulo=$((10#$modulo))
[ -n "$caminho" ] || { erro "caminho vazio"; exit 2; }

dir="${PLAB_HOME:-/opt/plab}/evidencias/$rel/menus"
mkdir -p "$dir"
tempo=${PLAB_MENUS_TEMPO:-1200}
limite=${PLAB_MENUS_LIMITE:-$((tempo + 300))}
echo "menus $rel: modulo $modulo, caminho '$caminho' (profundidade ${PLAB_MENUS_PROFUNDIDADE:-5}, tempo ${tempo}s)"
PLAB_MENUS_TEMPO=$tempo PYTHONPATH="${PLAB_HOME:-/opt/plab}/lab/tir${PYTHONPATH:+:$PYTHONPATH}" \
  timeout "$limite" python -u "${PLAB_HOME:-/opt/plab}/lab/tir/mapear_menu.py" "$rel" "$modulo" "$caminho" "$dir/$modulo.json"
rc=$?
[ "$rc" -eq 124 ] && erro "mapeamento cortado pelo limite de ${limite}s; a sessao pode ter ficado presa: plab restart $rel"
[ "$rc" -eq 4 ] && erro "saida por Log Off nao confirmada; libere a licenca com plab restart $rel"
echo "resumo menus $rel: rc=$rc json=$dir/$modulo.json"
exit "$rc"
