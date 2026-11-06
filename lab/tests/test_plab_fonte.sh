#!/usr/bin/env bash
# Testa a escolha da fonte das imagens pelo wrapper bash (issue #3) sem Docker: PLAB_<rel>_FONTE
# escolhe o compose (principal ou stacks/reserva/<rel>) e valor invalido para o comando.
#   test_plab_fonte.sh
set -uo pipefail
raiz=$(cd "$(dirname "$0")/../.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
falhas=0
confere() { # descricao obtido esperado
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FALHA $1: obtido [$2], esperado [$3]"; falhas=$((falhas + 1)); fi
}

{
  sed -n '/^RELEASES=/p; /^sair()/p' "$raiz/plab"
  sed -n '/^fonte()/,/^}/p; /^arquivo_compose()/,/^}/p; /^ler_env()/,/^}/p' "$raiz/plab"
} > "$tmp/funcoes.sh"

roda() { # conteudo-do-.env comando...
  printf '%s\n' "$1" > "$tmp/.env"; shift
  (cd "$tmp" && bash -c 'set -euo pipefail; RAIZ=$1; . "$2"; ler_env; shift 2; "$@"' _ "$tmp" "$tmp/funcoes.sh" "$@" 2>&1)
}

confere "sem variavel: principal" "$(roda '' arquivo_compose 2610)" "$tmp/stacks/2610/compose.yaml"
confere "principal explicita" "$(roda 'PLAB_2510_FONTE=principal' arquivo_compose 2510)" "$tmp/stacks/2510/compose.yaml"
confere "reserva 2610" "$(roda 'PLAB_2610_FONTE=reserva' arquivo_compose 2610)" "$tmp/stacks/reserva/2610/compose.yaml"
confere "reserva so na release pedida" "$(roda 'PLAB_2610_FONTE=reserva' arquivo_compose 2510)" "$tmp/stacks/2510/compose.yaml"
confere "lab nao muda" "$(roda 'PLAB_2610_FONTE=reserva' arquivo_compose lab)" "$tmp/lab/compose.yaml"
saida=$(roda 'PLAB_2510_FONTE=oficial' echo nao-chegou); rc=$?
confere "valor invalido para na leitura do .env" "$rc" 2
confere "mensagem do valor invalido" "$(grep -c "PLAB_2510_FONTE invalido" <<<"$saida")" 1

for rel in 2610 2510; do
  confere "compose da reserva $rel existe" "$([ -f "$raiz/stacks/reserva/$rel/compose.yaml" ] && echo sim)" sim
done

if [ "$falhas" -ne 0 ]; then echo "test_plab_fonte: $falhas falha(s)"; exit 1; fi
echo "test_plab_fonte: OK"
