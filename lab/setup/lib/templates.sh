#!/usr/bin/env bash
# Gera AGENTS.md, CLAUDE.md e GEMINI.md no workspace a partir de templates/agent-rules.md.tmpl.
# Escreve apenas dentro do bloco <!-- BEGIN plab --> ... <!-- END plab -->, preservando o resto
# do arquivo do usuario. Idempotente: mesma entrada gera os mesmos bytes.
gerar_instrucoes() { # release lista_skills(texto) [dir]
  local rel=$1 skills=$2 dir=${3:-/workspace}
  local tmpl="${PLAB_HOME:-/opt/plab}/templates/agent-rules.md.tmpl" bloco arq
  bloco=$(mktemp)
  {
    echo '<!-- BEGIN plab -->'
    sed -e "s/{{RELEASE}}/${rel}/g" "$tmpl" | awk -v s="$skills" '{ if ($0 == "{{SKILLS}}") print s; else print }'
    echo '<!-- END plab -->'
  } > "$bloco"
  for arq in AGENTS.md CLAUDE.md GEMINI.md; do
    local alvo="$dir/$arq" novo; novo=$(mktemp)
    if [ -f "$alvo" ] && grep -q '<!-- BEGIN plab -->' "$alvo"; then
      awk -v b="$bloco" '
        /<!-- BEGIN plab -->/ { while ((getline l < b) > 0) print l; pulando = 1; next }
        /<!-- END plab -->/   { pulando = 0; next }
        !pulando { print }' "$alvo" > "$novo"
    elif [ -f "$alvo" ]; then
      { cat "$alvo"; echo; cat "$bloco"; } > "$novo"
    else
      cat "$bloco" > "$novo"
    fi
    cmp -s "$novo" "$alvo" 2>/dev/null || cp "$novo" "$alvo"
    rm -f "$novo"
  done
  rm -f "$bloco"
}
