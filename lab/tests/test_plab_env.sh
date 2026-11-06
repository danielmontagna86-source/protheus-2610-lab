#!/usr/bin/env bash
# shellcheck disable=SC2016  # textos com $ literais, de proposito
# Testa a leitura do .env pelo wrapper bash (L3 da revisao) sem Docker: o arquivo e lido como
# dados, nada e executado nem exportado, e senhas nao sao lidas.
#   test_plab_env.sh
set -uo pipefail
raiz=$(cd "$(dirname "$0")/../.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
falhas=0
confere() { # descricao obtido esperado
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FALHA $1: obtido [$2], esperado [$3]"; falhas=$((falhas + 1)); fi
}

# Copia so as funcoes sair, fonte e ler_env do plab (o script executa o comando no fim).
{
  sed -n '/^RELEASES=/p; /^sair()/p' "$raiz/plab"
  sed -n '/^fonte()/,/^}/p' "$raiz/plab"
  sed -n '/^ler_env()/,/^}/p' "$raiz/plab"
} > "$tmp/funcoes.sh"

mkdir -p "$tmp/raiz"
cat > "$tmp/raiz/.env" <<'EOF'
# comentario
PLAB_2610_PORT_TCP=26234
PLAB_2510_PORT_TCP = 25234   # comentario inline
export PLAB_REINICIAR_APOS_COMPILAR="2510 2610"
PLAB_RENOVAR_SENHA_ADMIN=
PLAB_ADMIN_USER='Admin $HOME'
PLAB_CRLF=valor
PLAB_INJECAO=$(touch INJETADO)
PLAB_2610_ADMIN_PASSWORD=nao-pode-ser-lida
OUTRA_VAR=fora
PLAB_SO_COMENTARIO= # nada
PLAB_HASH_COLADO=a#b
PLAB_ULTIMA=sem-quebra-de-linha
EOF
sed -i 's/^PLAB_CRLF=valor$/PLAB_CRLF=valor\r/' "$tmp/raiz/.env"
printf 'PLAB_SEM_NL=fim' >> "$tmp/raiz/.env"

saida=$(cd "$tmp" && env -u PLAB_2610_ADMIN_PASSWORD bash -c '
  set -euo pipefail
  RAIZ=$1; . "$2"; ler_env
  printf "%s|" "$PLAB_2610_PORT_TCP" "$PLAB_2510_PORT_TCP" "$PLAB_REINICIAR_APOS_COMPILAR" \
    "${PLAB_RENOVAR_SENHA_ADMIN-unset}" "$PLAB_ADMIN_USER" "$PLAB_CRLF" "$PLAB_INJECAO" \
    "${PLAB_2610_ADMIN_PASSWORD-unset}" "${OUTRA_VAR-unset}" "$PLAB_SO_COMENTARIO" "$PLAB_HASH_COLADO" "$PLAB_SEM_NL"
  printf "%s" "$(env | grep -c "^PLAB_2610_PORT_TCP=" || true)"
' _ "$tmp/raiz" "$tmp/funcoes.sh")
IFS='|' read -r -a v <<<"$saida"
confere "valor simples" "${v[0]}" 26234
confere "espacos e comentario inline" "${v[1]}" 25234
confere "export e aspas duplas" "${v[2]}" "2510 2610"
confere "valor vazio continua definido" "${v[3]}" ""
confere "aspas simples sem expansao" "${v[4]}" 'Admin $HOME'
confere "CRLF removido" "${v[5]}" valor
confere "sem execucao de comando" "${v[6]}" '$(touch INJETADO)'
confere "arquivo do .env nao executado" "$([ -e "$tmp/INJETADO" ] && echo sim || echo nao)" nao
confere "senha nao lida" "${v[7]}" unset
confere "so variaveis PLAB_" "${v[8]}" unset
confere "valor so com comentario" "${v[9]}" ""
confere "# colado faz parte do valor" "${v[10]}" "a#b"
confere "ultima linha sem quebra" "${v[11]}" fim
confere "nada exportado" "${v[12]}" 0

# .env ausente: codigo 3
# shellcheck disable=SC1091,SC2034  # funcoes extraidas do plab em tempo de execucao
( RAIZ="$tmp/nao-existe"; . "$tmp/funcoes.sh"; ler_env ) 2>/dev/null
confere ".env ausente sai com 3" "$?" 3

echo "falhas: $falhas"
[ "$falhas" -eq 0 ]
