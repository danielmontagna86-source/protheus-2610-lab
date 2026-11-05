#!/usr/bin/env bash
# includes-semear.sh <dir> - roda num container auxiliar do 'plab includes', depois que os arquivos
# da pasta do usuario foram copiados (docker cp) para o volume montado em <dir>.
# O pre-compilador do advpls roda no Linux (sensivel a caixa): cada include ganha um link com o
# nome em maiusculas e outro em minusculas, para atender '#include "PROTHEUS.CH"' e "protheus.ch".
# A sentinela .plab-seeded so e gravada no fim, com a contagem.
set -euo pipefail
dst=${1:?informe o diretorio do volume}
cd "$dst"
find . -maxdepth 1 -iname 'prtopdef.ch' | grep -q . || { echo "includes-semear: PRTOPDEF.CH ausente em $dst" >&2; exit 4; }
chmod -R a+rX "$dst"
for f in *; do
  [ -f "$f" ] && [ ! -L "$f" ] || continue
  for alvo in "$(printf '%s' "$f" | tr '[:lower:]' '[:upper:]')" "$(printf '%s' "$f" | tr '[:upper:]' '[:lower:]')"; do
    if [ "$alvo" != "$f" ] && [ ! -e "$alvo" ]; then ln -s "$f" "$alvo"; fi
  done
done
n=$(find . -maxdepth 1 -type f -iname '*.ch' | wc -l)
printf 'includes=%s criado=%s\n' "$n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > .plab-seeded
echo "includes-semear: $n arquivos .ch, $(find . -maxdepth 1 -type l | wc -l) links de caixa"
