#!/usr/bin/env bash
# shellcheck disable=SC2016  # stubs gravados com $ literais, de proposito
# Testa o passo 4 (limpeza) do lab smoke (L4 da revisao) sem container: doctor, interface e
# compile sao trocados por stubs; o secret vem de PLAB_SECRETS_DIR.
#   test_smoke_limpeza.sh
set -uo pipefail
raiz=$(cd "$(dirname "$0")/../.." && pwd)
tmp=$(mktemp -d)
ui_avulso=""
trap 'rm -rf "$tmp" ${ui_avulso:+"$ui_avulso"}' EXIT
falhas=0
confere() { # descricao obtido esperado
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FALHA $1: obtido [$2], esperado [$3]"; falhas=$((falhas + 1)); fi
}

home="$tmp/plab"; lib="$home/lab/bin/lib"
mkdir -p "$lib" "$home/evidencias" "$home/cenarios/hello" "$tmp/secrets"
cp "$raiz/lab/bin/lib/comum.sh" "$raiz/lab/bin/lib/smoke.sh" "$lib/"
printf '#!/bin/bash\nexit 0\n' > "$lib/doctor.sh"
# A interface grava nas evidencias o que estiver em UI_GRAVA (simula um vazamento).
printf '#!/bin/bash\nmkdir -p "$PLAB_EVID_DIR"; printf "%%b" "${UI_GRAVA:-tela ok}" > "$PLAB_EVID_DIR/ui.txt"\necho "[ui] OK: stub"\n' > "$lib/ui.sh"
printf '#!/bin/bash\necho "resumo compile stub SUCCESS=1"\n' > "$lib/compile.sh"
chmod +x "$lib"/*.sh
: > "$home/cenarios/hello/LABHELLO.prw"

roda() { # conteudo_do_secret [UI_GRAVA]
  printf '%b' "$1" > "$tmp/secrets/plab_2610_admin_password"
  PLAB_HOME="$home" PLAB_SECRETS_DIR="$tmp/secrets" UI_GRAVA="${2:-}" bash "$lib/smoke.sh" 2610 > "$tmp/saida" 2>&1
  echo $?
}

confere "limpo: PRONTO" "$(roda 'Senha123')" 0
confere "secret vazio: falha no passo 4" "$(roda '')" 14
confere "senha na evidencia: falha" "$(roda 'Senha123' 'x Senha123 y')" 14
confere "secret com CRLF ainda casa" "$(roda 'Senha123\r\n' 'x Senha123 y')" 14
confere "linha vazia no secret nao casa com tudo" "$(roda 'Senha123\n\n' 'tela ok')" 0
ui_avulso=$(mktemp -d /tmp/plab-ui-2610-teste.XXXXXX)
printf 'Senha123' > "$ui_avulso/captura.txt"
confere "senha em /tmp/plab-ui-*: falha" "$(roda 'Senha123')" 14
grep -q 'senha encontrada' "$tmp/saida"; confere "motivo informado" "$?" 0
rm -rf "$ui_avulso"; ui_avulso=""
confere "resumo.json sem a senha" "$(grep -rl 'Senha123' "$home/evidencias" --include=resumo.json | wc -l)" 0

echo "falhas: $falhas"
[ "$falhas" -eq 0 ]
