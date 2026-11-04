#!/usr/bin/env bash
# Testa lab menus / lab menus-diff sem container nem Protheus: codigos de saida de uso, JSON ausente e
# o relatorio gerado a partir das fixtures reais de Compras (lab/tests/fixtures/menus).
#   test_menus_cli.sh
set -uo pipefail
raiz=$(cd "$(dirname "$0")/../.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
falhas=0
confere() { # descricao obtido esperado
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FALHA $1: obtido [$2], esperado [$3]"; falhas=$((falhas + 1)); fi
}

home="$tmp/plab"
mkdir -p "$home/lab/bin/lib" "$home/lab/tir" "$home/evidencias" "$tmp/bin"
cp "$raiz/lab/bin/lab" "$home/lab/bin/"
cp "$raiz/lab/bin/lib/comum.sh" "$raiz/lab/bin/lib/menus.sh" "$raiz/lab/bin/lib/menus-diff.sh" "$home/lab/bin/lib/"
cp "$raiz/lab/tir/menus_diff.py" "$home/lab/tir/"
# o runner pode ter so python3; os scripts chamam "python", como no container lab
command -v python >/dev/null 2>&1 || ln -s "$(command -v python3)" "$tmp/bin/python"
export PATH="$tmp/bin:$PATH" PLAB_HOME="$home"
lab() { bash "$home/lab/bin/lab" "$@" > "$tmp/saida" 2>&1; echo $?; }

confere "menus sem release"            "$(lab menus)" 2
confere "menus release invalida"       "$(lab menus 2710 2)" 2
confere "menus modulo nao numerico"    "$(lab menus 2610 compras)" 2
confere "menus-diff sem modulo"        "$(lab menus-diff)" 2
confere "menus-diff modulo invalido"   "$(lab menus-diff 2x)" 2
confere "menus-diff sem os JSON"       "$(lab menus-diff 2)" 3
grep -q "rode lab menus 2610 2" "$tmp/saida"; confere "mensagem indica o lab menus" $? 0

for rel in 2610 2510; do mkdir -p "$home/evidencias/$rel/menus"; cp "$raiz/lab/tests/fixtures/menus/$rel/2.json" "$home/evidencias/$rel/menus/"; done
confere "menus-diff com as fixtures"   "$(lab menus-diff 02)" 0
rel="$home/evidencias/menus-diff-2.md"
confere "relatorio gerado" "$(test -s "$rel" && echo sim)" sim
grep -q "| Atualizações | Controle Orçamentário (6) |" "$rel"; confere "relatorio: so na 2610" $? 0
grep -q "| Atualizações | Cadastros | 30 | 28 | +2 |" "$rel"; confere "relatorio: contagem diferente" $? 0
grep -q "so 2610=1 so 2510=0 contagem diferente=1" "$tmp/saida"; confere "resumo na saida" $? 0

printf '{"menus": [' > "$home/evidencias/2510/menus/2.json"
confere "menus-diff com JSON invalido" "$(lab menus-diff 2)" 3

if [ "$falhas" -ne 0 ]; then echo "test_menus_cli: $falhas falha(s)"; exit 1; fi
echo "test_menus_cli: ok"
