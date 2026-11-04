#!/usr/bin/env bash
# lab menus-diff <modulo> - compara evidencias/2610/menus/<modulo>.json com evidencias/2510/menus/<modulo>.json
# (gerados pelo lab menus) e grava evidencias/menus-diff-<modulo>.md: itens so na 2610, so na 2510 e
# grupos com contagem diferente. Nao acessa o Protheus.
# Saida: 0 relatorio gerado; 2 uso invalido; 3 JSON ausente ou invalido.
set -uo pipefail
. "${PLAB_HOME:-/opt/plab}/lab/bin/lib/comum.sh"

modulo=${1:-}
case "$modulo" in
  ''|*[!0-9]*) erro "modulo invalido: '$modulo' (use o codigo numerico, ex.: 2 = Compras)"; exit 2 ;;
esac
modulo=$((10#$modulo))
evid="${PLAB_HOME:-/opt/plab}/evidencias"
for rel in 2610 2510; do
  [ -s "$evid/$rel/menus/$modulo.json" ] || { erro "falta $evid/$rel/menus/$modulo.json: rode lab menus $rel $modulo"; exit 3; }
done
python -B "${PLAB_HOME:-/opt/plab}/lab/tir/menus_diff.py" \
  "$evid/2610/menus/$modulo.json" "$evid/2510/menus/$modulo.json" "$evid/menus-diff-$modulo.md"
