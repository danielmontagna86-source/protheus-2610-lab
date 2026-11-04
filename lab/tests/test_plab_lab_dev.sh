#!/usr/bin/env bash
# Testa o modo desenvolvimento do lab no wrapper bash sem Docker: com PLAB_LAB_DEV=1 no .env o
# compose do lab ganha -f lab/compose.dev.yaml; sem a variavel (ou com 0) e nas releases, nao.
# Um "docker" falso no PATH so registra os argumentos.
#   test_plab_lab_dev.sh
set -uo pipefail
raiz=$(cd "$(dirname "$0")/../.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
falhas=0
confere() { # descricao obtido esperado
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FALHA $1: obtido [$2], esperado [$3]"; falhas=$((falhas + 1)); fi
}

mkdir -p "$tmp/raiz" "$tmp/bin"
cp "$raiz/plab" "$tmp/raiz/plab"
cat > "$tmp/bin/docker" <<'SH'
#!/usr/bin/env bash
[ "${1:-}" = info ] && exit 0
printf '%s\n' "$*" >> "$PLAB_TESTE_LOG"
SH
chmod +x "$tmp/bin/docker"

# roda "plab logs <alvo>" com o .env informado e devolve os -f usados (relativos a raiz)
arquivos() { # conteudo_env alvo
  printf '%s\n' "$1" > "$tmp/raiz/.env"
  : > "$tmp/log"
  PATH="$tmp/bin:$PATH" PLAB_TESTE_LOG="$tmp/log" env -u PLAB_LAB_DEV bash "$tmp/raiz/plab" logs "$2" >/dev/null 2>&1
  grep -o -- "-f [^ ]*" "$tmp/log" | sed "s#-f $tmp/raiz/##" | paste -sd' ' -
}

confere "lab sem a variavel"     "$(arquivos 'PLAB_ADMIN_USER=Admin' lab)"  "lab/compose.yaml"
confere "lab com PLAB_LAB_DEV=0" "$(arquivos 'PLAB_LAB_DEV=0' lab)"        "lab/compose.yaml"
confere "lab com PLAB_LAB_DEV=1" "$(arquivos 'PLAB_LAB_DEV=1' lab)"        "lab/compose.yaml lab/compose.dev.yaml"
confere "lab com aspas e comentario" "$(arquivos 'PLAB_LAB_DEV="1"   # dev' lab)" "lab/compose.yaml lab/compose.dev.yaml"
confere "2610 ignora PLAB_LAB_DEV=1" "$(arquivos 'PLAB_LAB_DEV=1' 2610)"   "stacks/2610/compose.yaml"
confere "2510 ignora PLAB_LAB_DEV=1" "$(arquivos 'PLAB_LAB_DEV=1' 2510)"   "stacks/2510/compose.yaml"
confere "override existe no repositorio" "$([ -f "$raiz/lab/compose.dev.yaml" ] && echo sim)" "sim"

echo "falhas: $falhas"
[ "$falhas" -eq 0 ]
