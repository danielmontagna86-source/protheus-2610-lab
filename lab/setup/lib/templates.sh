#!/usr/bin/env bash
# Gera AGENTS.md, CLAUDE.md e GEMINI.md no workspace a partir de templates/agent-rules.md.tmpl.
# Escreve apenas dentro do bloco <!-- BEGIN plab --> ... <!-- END plab -->, preservando o resto
# do arquivo do usuario. Idempotente: mesma entrada gera os mesmos bytes.
# So substitui com exatamente um BEGIN e um END, nessa ordem. Sem nenhum dos dois, acrescenta o
# bloco no fim. Qualquer outro caso (BEGIN sem END, END sem BEGIN, repetidos ou fora de ordem)
# perderia texto do usuario: avisa, nao grava esse arquivo e retorna 1 no fim.
gerar_instrucoes() { # release lista_skills(texto) [dir]
  local rel=$1 skills=$2 dir=${3:-/workspace}
  local tmpl="${PLAB_HOME:-/opt/plab}/templates/agent-rules.md.tmpl" bloco arq ret=0
  bloco=$(mktemp)
  {
    echo '<!-- BEGIN plab -->'
    sed -e "s/{{RELEASE}}/${rel}/g" "$tmpl" | awk -v s="$skills" '{ if ($0 == "{{SKILLS}}") print s; else print }'
    echo '<!-- END plab -->'
  } > "$bloco"
  for arq in AGENTS.md CLAUDE.md GEMINI.md; do
    local alvo="$dir/$arq" novo nb=0 ne=0 lb=0 le=0
    if [ -f "$alvo" ]; then
      nb=$(grep -cF '<!-- BEGIN plab -->' "$alvo"); ne=$(grep -cF '<!-- END plab -->' "$alvo")
      lb=$(grep -nF -m1 '<!-- BEGIN plab -->' "$alvo" | cut -d: -f1); le=$(grep -nF -m1 '<!-- END plab -->' "$alvo" | cut -d: -f1)
    fi
    novo=$(mktemp)
    if [ "$nb" -eq 1 ] && [ "$ne" -eq 1 ] && [ "${lb:-0}" -lt "${le:-0}" ]; then
      awk -v b="$bloco" '
        index($0, "<!-- BEGIN plab -->") { while ((getline l < b) > 0) print l; pulando = 1; next }
        index($0, "<!-- END plab -->")   { pulando = 0; next }
        !pulando { print }' "$alvo" > "$novo"
    elif [ "$nb" -eq 0 ] && [ "$ne" -eq 0 ] && [ -f "$alvo" ]; then
      { cat "$alvo"; echo; cat "$bloco"; } > "$novo"
    elif [ ! -f "$alvo" ]; then
      cat "$bloco" > "$novo"
    else
      echo "  aviso: $alvo tem marcadores do bloco plab incompletos (BEGIN=$nb, END=$ne);" \
           "arquivo NAO alterado. Deixe um '<!-- BEGIN plab -->' e um '<!-- END plab -->' (ou nenhum) e rode de novo." >&2
      rm -f "$novo"; ret=1; continue
    fi
    cmp -s "$novo" "$alvo" 2>/dev/null || cp "$novo" "$alvo"
    rm -f "$novo"
  done
  rm -f "$bloco"
  return "$ret"
}
