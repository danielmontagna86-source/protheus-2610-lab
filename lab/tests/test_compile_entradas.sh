#!/usr/bin/env bash
# shellcheck disable=SC2016  # stub gravado com $ literais, de proposito
# Testa entradas atipicas do lab compile (L5 da revisao) sem container: o advpls e um stub e o
# secret vem de PLAB_SECRETS_DIR.
#   test_compile_entradas.sh
set -uo pipefail
raiz=$(cd "$(dirname "$0")/../.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
falhas=0
confere() { # descricao obtido esperado
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FALHA $1: obtido [$2], esperado [$3]"; falhas=$((falhas + 1)); fi
}

home="$tmp/plab"
mkdir -p "$home/lab/bin/lib" "$tmp/bin" "$tmp/secrets" "$tmp/inc" "$tmp/fontes/a" "$tmp/fontes/b"
cp "$raiz/lab/bin/lib/comum.sh" "$raiz/lab/bin/lib/compile.sh" "$home/lab/bin/lib/"
: > "$tmp/inc/PRTOPDEF.CH"
# advpls falso: guarda uma copia do script (para conferir a codificacao) e da SUCCESS por fonte.
printf '#!/bin/bash\ncp "$2" "$STUB_COPIA"\nlinha=$(grep -a "^program=" "$2"); IFS=, read -r -a fs <<<"${linha#program=}"\nfor f in "${fs[@]}"; do echo "[SUCCESS] $f"; done\n' > "$tmp/bin/advpls"
chmod +x "$tmp/bin/advpls"
for f in a/um.prw a/dois.prw b/UM.PRW "a/com,virgula.prw" "a/com espaco.prw"; do printf 'x\r\n' > "$tmp/fontes/$f"; done

roda() { # senha fontes...
  local senha=$1; shift
  printf '%s' "$senha" > "$tmp/secrets/plab_2610_admin_password"
  rm -f "$tmp/copia"
  PATH="$tmp/bin:$PATH" PLAB_HOME="$home" PLAB_SECRETS_DIR="$tmp/secrets" PLAB_INCLUDES="$tmp/inc" \
    PLAB_2610_HOST=appserver-2610 PLAB_2610_ENV_COMPILA=P2610_COMPILA STUB_COPIA="$tmp/copia" \
    bash "$home/lab/bin/lib/compile.sh" 2610 "$@" > "$tmp/saida" 2>&1
  echo $?
}

confere "dois fontes: OK" "$(roda 'Senha123' "$tmp/fontes/a/um.prw" "$tmp/fontes/a/dois.prw")" 0
confere "program= com os dois" "$(grep -ac '^program=.*um.prw,.*dois.prw' "$tmp/copia")" 1
confere "senha com acento vira CP1252" "$(roda 'Senhaé1' "$tmp/fontes/a/um.prw"; grep -ac $'^psw=Senha\xe91' "$tmp/copia")" "0
1"
confere "nome com virgula: codigo 2" "$(roda 'Senha123' "$tmp/fontes/a/com,virgula.prw")" 2
confere "nome com espaco: codigo 2" "$(roda 'Senha123' "$tmp/fontes/a/com espaco.prw")" 2
confere "mesmo nome em pastas diferentes: codigo 2" "$(roda 'Senha123' "$tmp/fontes/a/um.prw" "$tmp/fontes/b/UM.PRW")" 2
grep -q 'mesmo nome' "$tmp/saida"; confere "duplicado: motivo informado" "$?" 0
confere "senha fora do CP1252: codigo 23" "$(roda 'Senhał1' "$tmp/fontes/a/um.prw")" 23
confere "senha fora do CP1252: advpls nao roda" "$([ -e "$tmp/copia" ] && echo rodou || echo nao)" nao
confere "senha fora do CP1252: senha fora da saida" "$(grep -c 'Senha' "$tmp/saida")" 0
confere "sem temporario sobrando" "$(find /tmp -maxdepth 1 -name 'plab-compile.*' -newer "$tmp/secrets" | wc -l)" 0

echo "falhas: $falhas"
[ "$falhas" -eq 0 ]
