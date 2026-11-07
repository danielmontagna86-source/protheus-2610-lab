#!/usr/bin/env bash
# Testa o ajuste das sequencias de RECNO do wrapper bash (issue #30) sem Docker: o banco e trocado
# por um stub de sequencias_recno. Confere quais releases rodam (PLAB_AJUSTAR_SEQUENCIAS, fonte),
# o registro em evidencias/<rel>/ e o retorno em falha. Confere tambem o SQL: o ajuste so adianta.
#   test_plab_sequencias.sh
set -uo pipefail
raiz=$(cd "$(dirname "$0")/../.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
falhas=0
confere() { # descricao obtido esperado
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FALHA $1: obtido [$2], esperado [$3]"; falhas=$((falhas + 1)); fi
}

sed -n '/^sair()/p; /^fonte()/,/^}/p; /^ajustar_sequencias()/,/^}/p' "$raiz/plab" > "$tmp/funcoes.sh"

roda() { # saida-do-banco(ou FALHA) variaveis... -- comando...
  local banco=$1 vars=(); shift
  while [ "$1" != -- ]; do vars+=("$1"); shift; done; shift
  # shellcheck disable=SC2016 # o script do bash -c expande os proprios argumentos, de proposito
  (cd "$tmp" && env "${vars[@]}" bash -c '
    set -euo pipefail; RAIZ=$1; BANCO=$2; . "$3"; shift 3
    sequencias_recno() { # stub: o comando real vai ao banco da release
      [ "$BANCO" = FALHA ] && { echo "psql: erro simulado"; return 1; }
      [ "$2" = true ] || return 9
      [ -n "$BANCO" ] && printf "%s\n" "$BANCO"
      return 0
    }
    "$@"' _ "$tmp" "$banco" "$tmp/funcoes.sh" "$@" 2>&1)
}

atrasadas=$'sys_usr|sys_usr_r_e_c_n_o__seq|1|2\nsys_company|sys_company_r_e_c_n_o__seq|1|2'

saida=$(roda "$atrasadas" -- ajustar_sequencias 2610)
confere "2610 por padrao: ajusta e conta" "$(grep -c 'ajustadas em plab-2610: 2 tabela' <<<"$saida")" 1
arq=$(find "$tmp/evidencias/2610" -name 'sequencias-*.txt' 2>/dev/null | head -n 1)
confere "registro gravado em evidencias/2610" "$([ -n "$arq" ] && echo sim)" sim
confere "registro com cabecalho e as tabelas" "$(wc -l < "${arq:-/dev/null}" | tr -d ' ')" 4
confere "registro traz a tabela" "$(grep -c '^sys_usr|' "${arq:-/dev/null}")" 1
rm -rf "$tmp/evidencias"

confere "2510 fora do padrao: nada" "$(roda "$atrasadas" -- ajustar_sequencias 2510)" ""
confere "lista vazia desliga" "$(roda "$atrasadas" PLAB_AJUSTAR_SEQUENCIAS= -- ajustar_sequencias 2610)" ""
confere "lista com 2510" "$(roda "$atrasadas" 'PLAB_AJUSTAR_SEQUENCIAS=2610 2510' -- ajustar_sequencias 2510 | grep -c 'ajustadas em plab-2510')" 1
confere "fonte reserva: nada" "$(roda "$atrasadas" PLAB_2610_FONTE=reserva -- ajustar_sequencias 2610)" ""
confere "forcar ignora lista e fonte" "$(roda "$atrasadas" PLAB_AJUSTAR_SEQUENCIAS= PLAB_2610_FONTE=reserva -- ajustar_sequencias 2610 forcar | grep -c ajustadas)" 1
rm -rf "$tmp/evidencias"

confere "nada atrasado: em dia" "$(roda '' -- ajustar_sequencias 2610)" "sequencias de RECNO em dia em plab-2610"
confere "nada atrasado: sem registro" "$([ -d "$tmp/evidencias" ] && echo sim || echo nao)" nao

saida=$(roda FALHA -- ajustar_sequencias 2610); rc=$?
confere "falha do banco: retorno 1" "$rc" 1
confere "falha do banco: aviso" "$(grep -c 'ajuste das sequencias de RECNO falhou' <<<"$saida")" 1

sql="$raiz/stacks/sql/ajusta-sequencias-recno.sql"
confere "SQL: so tabelas atrasadas" "$(grep -c 'WHERE proximo <= maior' "$sql")" 1
confere "SQL: setval para o maior RECNO" "$(grep -c 'setval(seq, maior, true)' "$sql")" 1
confere "SQL: setval so com ajustar" "$(grep -c 'CASE WHEN :ajustar THEN setval' "$sql")" 1
confere "SQL: nenhum UPDATE/DELETE/INSERT" "$(grep -ciE '^\s*(update|delete|insert)\b' "$sql")" 0

if [ "$falhas" -ne 0 ]; then echo "test_plab_sequencias: $falhas falha(s)"; exit 1; fi
echo "test_plab_sequencias: OK"
