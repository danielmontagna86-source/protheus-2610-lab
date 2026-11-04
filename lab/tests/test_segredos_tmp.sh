#!/usr/bin/env bash
# shellcheck disable=SC2016  # textos com $ literais, de proposito
# Testa os temporarios de segredo e de estado do "lab setup" (L7 da revisao) sem container:
# nada passa por TMPDIR, o diretorio vira 700 sem depender de estado_iniciar, nao sobra temporario
# e a variavel nao duplica.
#   test_segredos_tmp.sh
set -uo pipefail
raiz=$(cd "$(dirname "$0")/../.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
falhas=0
confere() { # descricao obtido esperado
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FALHA $1: obtido [$2], esperado [$3]"; falhas=$((falhas + 1)); fi
}
mkdir -p "$tmp/home" "$tmp/tmpdir"

HOME="$tmp/home" TMPDIR="$tmp/tmpdir" bash -c '
  set -uo pipefail
  . "$1/lab/setup/lib/segredos.sh"
  segredos_preparar
  stat -c %a "$HOME/.config/lab" > "$2/modo_dir"
  printf "segredo-1\n" | segredo_ler LAB_TESTE_KEY "chave" >/dev/null 2>&1
  printf "segredo 2\$x\n" | segredo_ler LAB_TESTE_KEY "chave" >/dev/null 2>&1
  printf "outro\n" | segredo_ler OUTRA_KEY "chave" >/dev/null 2>&1
  segredo_valor LAB_TESTE_KEY > "$2/valor"
  . "$1/lab/setup/lib/estado.sh"
  estado_iniciar
  estado_set ".release" "2610"
  estado_set ".ias.x.estado" "testado_ok"
  if estado_jq "invalido(" 2>/dev/null; then echo passou; else echo falhou; fi > "$2/rc_jq"
' _ "$raiz" "$tmp"

cfg="$tmp/home/.config/lab"
confere "diretorio 700 so com segredos_preparar" "$(cat "$tmp/modo_dir")" 700
confere "secrets.env 600" "$(stat -c '%a' "$cfg/secrets.env")" 600
confere "variavel sem duplicar" "$(grep -c '^LAB_TESTE_KEY=' "$cfg/secrets.env")" 1
confere "outra variavel preservada" "$(grep -c '^OUTRA_KEY=' "$cfg/secrets.env")" 1
confere "valor com espaco e \$ preservado" "$(cat "$tmp/valor")" 'segredo 2$x'
confere "nada em TMPDIR" "$(find "$tmp/tmpdir" -mindepth 1 | wc -l)" 0
confere "nenhum temporario sobrando no diretorio" "$(find "$cfg" -name '.secrets.*' -o -name '.state.*' | wc -l)" 0
confere "estado gravado" "$(jq -r '.release + " " + .ias.x.estado' "$cfg/state.json")" "2610 testado_ok"
confere "filtro jq invalido falha" "$(cat "$tmp/rc_jq")" falhou
confere "state.json intacto apos falha" "$(jq -r .release "$cfg/state.json")" 2610

echo "falhas: $falhas"
[ "$falhas" -eq 0 ]
