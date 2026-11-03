#!/usr/bin/env bash
# Testa stacks/semear-volume.sh (L1 da revisao) sem Docker: semeadura nova, reexecucao,
# semeadura interrompida e volume de versao anterior (sem sentinela).
#   test_semear_volume.sh
set -euo pipefail
raiz=$(cd "$(dirname "$0")/../.." && pwd)
semear="$raiz/stacks/semear-volume.sh"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
falhas=0
confere() { # descricao condicao...
  local d=$1; shift
  if "$@"; then echo "ok   $d"; else echo "FALHA $d"; falhas=$((falhas + 1)); fi
}

src="$tmp/src"; mkdir -p "$src/sub"
printf 'rpo original' > "$src/tttm120.rpo"
printf 'a' > "$src/a.ch"
printf 'b' > "$src/sub/b.ch"

# 1. volume vazio
dst="$tmp/v1"
bash "$semear" "$src" "$dst" tttm120.rpo t1 >/dev/null
confere "semeadura nova grava a sentinela" test -f "$dst/.plab-seeded"
confere "semeadura nova nao deixa a marca de andamento" test ! -e "$dst/.plab-seeding"
confere "semeadura nova copia tudo" diff -r --exclude=.plab-seeded "$src" "$dst"

# 2. reexecucao nao toca no volume (RPO com fonte compilado continua)
printf 'rpo com fonte compilado' > "$dst/tttm120.rpo"
bash "$semear" "$src" "$dst" tttm120.rpo t1 >/dev/null
confere "reexecucao preserva o RPO" grep -q 'compilado' "$dst/tttm120.rpo"

# 3. semeadura interrompida: marca de andamento + copia parcial (RPO truncado)
dst="$tmp/v3"; mkdir -p "$dst"
: > "$dst/.plab-seeding"
printf 'rpo trunc' > "$dst/tttm120.rpo"
bash "$semear" "$src" "$dst" tttm120.rpo t3 >/dev/null
confere "interrompida: RPO copiado de novo" cmp -s "$src/tttm120.rpo" "$dst/tttm120.rpo"
confere "interrompida: arquivos que faltavam copiados" test -f "$dst/sub/b.ch"
confere "interrompida: sentinela gravada" test -f "$dst/.plab-seeded"
confere "interrompida: marca de andamento removida" test ! -e "$dst/.plab-seeding"

# 4. volume de versao anterior: tem a marca, nao tem sentinela; completa sem sobrescrever
dst="$tmp/v4"; mkdir -p "$dst"
printf 'rpo com fonte compilado' > "$dst/tttm120.rpo"
ln -s a.ch "$dst/A.CH"
bash "$semear" "$src" "$dst" tttm120.rpo t4 >/dev/null
confere "anterior: RPO preservado" grep -q 'compilado' "$dst/tttm120.rpo"
confere "anterior: arquivos faltantes copiados" test -f "$dst/a.ch" -a -f "$dst/sub/b.ch"
confere "anterior: link existente preservado" test -L "$dst/A.CH"
confere "anterior: sentinela gravada" test -f "$dst/.plab-seeded"

# 5. falha na copia nao grava a sentinela
dst="$tmp/v5"
if bash "$semear" "$tmp/nao-existe" "$dst" tttm120.rpo t5 >/dev/null 2>&1; then
  confere "origem ausente falha" false
else
  confere "origem ausente falha" true
fi
confere "origem ausente: sem sentinela" test ! -e "$dst/.plab-seeded"

echo "falhas: $falhas"
[ "$falhas" -eq 0 ]
