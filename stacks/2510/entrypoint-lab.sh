#!/bin/bash
# Entrypoint do lab para o AppServer 2510: da ao ambiente de compilacao P2510D um RPO proprio
# (/protheus12/apo_compila, volume semeado pelo rpo-init), como o P2610_COMPILA da 2610.
# Motivo (verificado em 02/11/2026): na imagem, P2510D compartilha o RPO de P2510; compilar nele faz
# o AppServer parar e religar os servidores HTTP, o REST pega a porta aleatoria do servidor interno
# do /app-root ("error starting HTTP server SD") e a tela de login nova fica fora ate reiniciar.
# So as chaves SourcePath/RPOCustom/RPOTLPP da secao [P2510D] mudam; o resto do .ini e preservado.
set -euo pipefail
ini=/protheus12/bin/appserver/appserver.ini
awk '
  { cr = ($0 ~ /\r$/) ? "\r" : ""; linha = $0; sub(/\r$/, "", linha) }
  linha ~ /^\[.*\]$/ { secao = toupper(linha) }
  secao == "[P2510D]" && linha ~ /^SourcePath=/ { print "SourcePath=/protheus12/apo_compila" cr; next }
  secao == "[P2510D]" && linha ~ /^RPOCustom=/  { print "RPOCustom=/protheus12/apo_compila/custom.rpo" cr; next }
  secao == "[P2510D]" && linha ~ /^RPOTLPP=/    { print "RPOTLPP=/protheus12/apo_compila/tlpp.rpo" cr; next }
  { print }
' "$ini" > /tmp/appserver.ini.lab
cat /tmp/appserver.ini.lab > "$ini"
rm -f /tmp/appserver.ini.lab
echo "plab: P2510D usando RPO proprio em /protheus12/apo_compila"
exec /protheus.sh
