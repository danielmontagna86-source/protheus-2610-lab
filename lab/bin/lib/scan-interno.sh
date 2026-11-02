#!/usr/bin/env bash
# scan-interno.sh - parte da varredura de segredos que roda DENTRO do container lab (plab scan).
# Le os valores sensiveis que so existem aqui (senhas em /run/secrets, chaves em
# ~/.config/lab/secrets.env, tokens das credenciais do Claude Code e do Codex) e procura esses
# valores em arquivos ou na entrada padrao. Nunca imprime valor: so "<item> <ocorrencias>".
#   scan-interno.sh arquivos   -> varre os locais do container (lista abaixo)
#   scan-interno.sh stdin      -> conta ocorrencias no texto recebido (ex.: docker logs do host)
set -uo pipefail
modo=${1:-arquivos}

valores=$(mktemp /tmp/plab-scan.XXXXXX); chmod 600 "$valores"
trap 'rm -f "$valores"' EXIT

# Senhas do Admin (secrets do compose).
for s in /run/secrets/plab_*_admin_password; do
  [ -r "$s" ] && tr -d '\r\n' < "$s" && echo
done >> "$valores"
# Chaves do assistente (formato VAR=valor, sem aspas).
[ -r "$HOME/.config/lab/secrets.env" ] && sed -nE 's/^[A-Z0-9_]+=(.+)$/\1/p' "$HOME/.config/lab/secrets.env" >> "$valores"
# Tokens das CLIs: valores de campos cujo nome indica token, chave ou segredo (ex.: accessToken,
# refresh_token, OPENAI_API_KEY). IDs de conta e organizacao nao sao segredos e ficam de fora.
for c in "$HOME/.claude/.credentials.json" "$HOME/.codex/auth.json"; do
  [ -r "$c" ] && python3 -c '
import json, re, sys
sensivel = re.compile(r"token|key|secret|password", re.I)
def walk(o, chave=""):
    if isinstance(o, dict):
        for k, v in o.items(): walk(v, k)
    elif isinstance(o, list):
        for v in o: walk(v, chave)
    elif isinstance(o, str) and sensivel.search(chave) and len(o) >= 20:
        print(o)
walk(json.load(open(sys.argv[1])))' "$c" >> "$valores" 2>/dev/null
done
# So valores com 6+ caracteres (evita falso positivo com textos curtos).
awk 'length >= 6' "$valores" | sort -u > "$valores.f" && mv "$valores.f" "$valores"
total_valores=$(wc -l < "$valores")

contar() { if [ -s "$valores" ]; then { grep -aoF -f "$valores" || true; } | wc -l; else cat >/dev/null; echo 0; fi; }

if [ "$modo" = stdin ]; then
  echo "stdin $(contar) valores=$total_valores"
  exit 0
fi

# Locais onde um segredo NAO deve aparecer. Os proprios arquivos de credencial ficam de fora.
item() { # rotulo caminho...
  local rotulo=$1; shift
  local n
  n=$(find "$@" -type f ! -path "$HOME/.claude/.credentials.json" ! -path "$HOME/.codex/auth.json" \
        ! -path "$HOME/.config/lab/secrets.env" ! -path '*/node_modules/*' ! -path "$HOME/.npm-global/*" \
        ! -path "$valores" ! -path '/tmp/plab-scan.*' \
        -size -20M -print0 2>/dev/null | xargs -0 -r cat 2>/dev/null | contar)
  echo "$rotulo ${n:-0}"
}
item workspace /workspace
item evidencias /opt/plab/evidencias
item estado-do-setup "$HOME/.config/lab"
item historico-do-shell "$HOME/.bash_history"
item logs-npm "$HOME/.npm/_logs"
item config-claude "$HOME/.claude" "$HOME/.claude.json"
item config-codex "$HOME/.codex"
item temporarios /tmp
echo "valores $total_valores"
