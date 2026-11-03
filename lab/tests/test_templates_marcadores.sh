#!/usr/bin/env bash
# Testa o bloco plab de AGENTS/CLAUDE/GEMINI.md (L8 da revisao) sem container: so substitui com
# um BEGIN e um END em ordem; nos outros casos o arquivo do usuario fica intacto.
#   test_templates_marcadores.sh
set -uo pipefail
raiz=$(cd "$(dirname "$0")/../.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
falhas=0
confere() { # descricao obtido esperado
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FALHA $1: obtido [$2], esperado [$3]"; falhas=$((falhas + 1)); fi
}
# shellcheck source=lab/setup/lib/templates.sh
. "$raiz/lab/setup/lib/templates.sh"
export PLAB_HOME="$raiz"

caso() { # nome conteudo_inicial_do_AGENTS.md (vazio = arquivo ausente) -> imprime o rc
  local d="$tmp/$1"; mkdir -p "$d"
  [ -n "$2" ] && printf '%b' "$2" > "$d/AGENTS.md"
  gerar_instrucoes 2610 "- \`skill\`" "$d" 2> "$d/avisos"
  echo $?
}
B='<!-- BEGIN plab -->'; E='<!-- END plab -->'

confere "arquivo novo: rc 0" "$(caso novo '')" 0
confere "arquivo novo: tem o bloco" "$(grep -c -e "$B" -e "$E" "$tmp/novo/AGENTS.md")" 2

confere "sem marcadores: rc 0" "$(caso sem "texto do usuario\n")" 0
confere "sem marcadores: texto preservado e bloco no fim" \
  "$(head -n1 "$tmp/sem/AGENTS.md"; tail -n1 "$tmp/sem/AGENTS.md")" "texto do usuario
$E"
cp "$tmp/sem/AGENTS.md" "$tmp/antes"; gerar_instrucoes 2610 "- \`skill\`" "$tmp/sem"
confere "sem marcadores: reexecucao idempotente" "$(cmp -s "$tmp/antes" "$tmp/sem/AGENTS.md" && echo igual)" igual

confere "par completo: rc 0" "$(caso par "antes\n$B\nvelho\n$E\ndepois\n")" 0
confere "par completo: substitui so o bloco" \
  "$(head -n1 "$tmp/par/AGENTS.md"; tail -n1 "$tmp/par/AGENTS.md"; grep -c velho "$tmp/par/AGENTS.md")" "antes
depois
0"

for c in "begin-sem-end|antes\n$B\nmeu texto depois\n" \
         "end-sem-begin|antes\n$E\nmeu texto\n" \
         "fora-de-ordem|$E\nmeio\n$B\nfim\n" \
         "repetido|$B\na\n$E\n$B\nb\n$E\nfim\n" \
         "mesma-linha|x $B $E y\nfim\n"; do
  nome=${c%%|*}; conteudo=${c#*|}
  printf '%b' "$conteudo" > "$tmp/esperado"
  confere "$nome: rc 1" "$(caso "$nome" "$conteudo")" 1
  confere "$nome: arquivo intacto" "$(cmp -s "$tmp/esperado" "$tmp/$nome/AGENTS.md" && echo intacto)" intacto
  confere "$nome: aviso" "$(grep -c 'NAO alterado' "$tmp/$nome/avisos")" 1
  confere "$nome: os outros arquivos foram gerados" "$(find "$tmp/$nome" -name CLAUDE.md -o -name GEMINI.md | wc -l)" 2
done

echo "falhas: $falhas"
[ "$falhas" -eq 0 ]
