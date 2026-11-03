#!/usr/bin/env bash
# semear-volume.sh <origem> <destino> <arquivo-marca> <nome>
# Semeia um volume nomeado UMA vez (servicos *-init dos compose), com sentinela gravada so no fim.
#   - <destino>/.plab-seeded   : semeadura completa; nada a fazer.
#   - <destino>/.plab-seeding  : semeadura anterior interrompida; copia tudo de novo, sobrescrevendo.
#   - sem sentinela, mas com <arquivo-marca>: volume de versao anterior do lab (semeado sem
#     sentinela). Completa so o que faltar, sem sobrescrever (o RPO pode ter fontes compilados).
#   - volume vazio: semeadura normal.
# Montado somente leitura nos servicos *-init; roda como /bin/bash na imagem AppServer.
set -euo pipefail

origem=${1:?origem}; destino=${2:?destino}; marca=${3:?arquivo-marca}; nome=${4:-semear}
feito="$destino/.plab-seeded"
andamento="$destino/.plab-seeding"

[ -d "$origem" ] || { echo "$nome: origem ausente: $origem" >&2; exit 1; }
mkdir -p "$destino"

if [ -f "$feito" ]; then
  echo "$nome: volume ja semeado, nada a fazer"
  exit 0
fi

if [ ! -e "$andamento" ] && [ -e "$destino/$marca" ]; then
  # Copia so o que falta, arquivo a arquivo (cp -n muda de codigo de saida entre versoes do coreutils).
  n=0
  while IFS= read -r -d '' rel; do
    rel=${rel#./}
    if [ ! -e "$destino/$rel" ] && [ ! -L "$destino/$rel" ]; then
      mkdir -p "$destino/$(dirname "$rel")"
      cp -a "$origem/$rel" "$destino/$rel"
      n=$((n + 1))
    fi
  done < <(cd "$origem" && find . -mindepth 1 ! -type d -print0)
  echo "$nome: volume de versao anterior; $n arquivo(s) faltante(s) copiado(s), nada sobrescrito"
else
  [ -e "$andamento" ] && echo "$nome: semeadura anterior interrompida; copiando de novo"
  : > "$andamento"
  cp -a "$origem/." "$destino/"
  echo "$nome: volume semeado a partir de $origem"
fi

: > "$feito"
rm -f "$andamento"
