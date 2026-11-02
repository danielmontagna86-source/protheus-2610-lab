#!/usr/bin/env bash
# Provider Claude Code para o "lab setup".
# Fontes (consultadas em 02/11/2026): code.claude.com/docs/en/setup e /authentication e /skills.
#  - pacote npm @anthropic-ai/claude-code (Node 22+);
#  - conta: "claude auth login" (mostra URL para copiar e aceita o codigo colado: funciona no container);
#  - chave: ANTHROPIC_API_KEY (ou CLAUDE_CODE_OAUTH_TOKEN gerado por "claude setup-token");
#  - credencial da conta em ~/.claude/.credentials.json (0600); skills em ~/.claude/skills/<nome>/SKILL.md.

CLAUDE_PACOTE="@anthropic-ai/claude-code"
CLAUDE_DIR_SKILLS="${HOME}/.claude/skills"

claude_instalar() {
  local versao=${PLAB_CLAUDE_CODE:?PLAB_CLAUDE_CODE nao definido}
  if [ "$(npm ls -g --prefix "$NPM_PREFIXO" --depth 0 --json 2>/dev/null | jq -r --arg p "$CLAUDE_PACOTE" '.dependencies[$p].version // empty')" = "$versao" ]; then
    echo "  claude: ${CLAUDE_PACOTE}@${versao} ja instalado"
  else
    npm install -g --prefix "$NPM_PREFIXO" --no-audit --no-fund "${CLAUDE_PACOTE}@${versao}" >/dev/null || return 1
    echo "  claude: ${CLAUDE_PACOTE}@${versao} instalado"
  fi
  # Wrapper: carrega SO a variavel da Claude (se a chave foi escolhida) e chama o binario real.
  mkdir -p "${HOME}/.local/bin"
  cat > "${HOME}/.local/bin/claude" <<EOF
#!/usr/bin/env bash
# gerado por lab setup: carrega apenas ANTHROPIC_API_KEY de ~/.config/lab/secrets.env, se existir
if grep -q '^ANTHROPIC_API_KEY=' "\$HOME/.config/lab/secrets.env" 2>/dev/null; then
  export ANTHROPIC_API_KEY="\$(set -a; . "\$HOME/.config/lab/secrets.env"; printf '%s' "\$ANTHROPIC_API_KEY")"
fi
exec "${NPM_PREFIXO}/bin/claude" "\$@"
EOF
  chmod 755 "${HOME}/.local/bin/claude"
}

claude_autenticar() { # modo: conta|api_key ; interativo: 1|0
  local modo=$1 interativo=$2
  case "$modo" in
    api_key)
      if segredo_existe ANTHROPIC_API_KEY && [ "$interativo" = 1 ]; then
        read -r -p "  ja existe chave da Claude; substituir? [s/N] " r; [ "$r" = s ] || return 0
      elif segredo_existe ANTHROPIC_API_KEY; then return 0; fi
      [ "$interativo" = 1 ] || { return 2; }
      segredo_ler ANTHROPIC_API_KEY "  ANTHROPIC_API_KEY" || return 2 ;;
    conta)
      [ -s "${HOME}/.claude/.credentials.json" ] && { echo "  claude: login de conta ja existe"; return 0; }
      [ "$interativo" = 1 ] || { return 2; }
      echo "  claude: copie a URL que aparece depois de 'visit:', abra no navegador, entre e autorize;"
      echo "          depois cole o codigo mostrado pelo navegador em 'Paste code here' e tecle Enter."
      "${HOME}/.local/bin/claude" auth login || return 1 ;;
  esac
}

claude_testar() {
  local saida
  saida=$(timeout 120 "${HOME}/.local/bin/claude" -p "Responda apenas: OK" 2>&1) || { echo "falhou: ${saida:0:160}"; return 1; }
  grep -q 'OK' <<<"$saida" || { echo "resposta inesperada: ${saida:0:160}"; return 1; }
}

claude_dir_skills() { echo "$CLAUDE_DIR_SKILLS"; }
