#!/usr/bin/env bash
# Provider opencode para o "lab setup".
# Fontes (consultadas em 02/11/2026; ver research.md R-07): opencode.ai/docs/cli, /providers,
# /skills e /rules (lidas no repositorio oficial sst/opencode, packages/web/src/content/docs).
#  - pacote npm opencode-ai; atualizacao automatica desligada por OPENCODE_DISABLE_AUTOUPDATE;
#  - conta: "opencode auth login" (o usuario escolhe o provedor e o metodo; GitHub Copilot usa
#    codigo de dispositivo; fluxos que abrem navegador local nao sao garantidos no container);
#  - chave: variavel de ambiente do provedor (OPENCODE_API_KEY ou ANTHROPIC_API_KEY), carregada
#    so pelo wrapper; o "auth login" nao le chave por stdin, entao a chave nao passa por ele;
#  - credencial do "auth login" em ~/.local/share/opencode/auth.json;
#  - skills em ~/.config/opencode/skills/<nome>/SKILL.md (tambem le ~/.claude/skills e
#    ~/.agents/skills); instrucoes: AGENTS.md do projeto (CLAUDE.md so se nao houver AGENTS.md).

OPENCODE_PACOTE="opencode-ai"
OPENCODE_DIR_SKILLS="${HOME}/.config/opencode/skills"
OPENCODE_AUTH="${HOME}/.local/share/opencode/auth.json"
# Provedores com variavel de chave documentada: <provedor>=<VARIAVEL>
OPENCODE_CHAVES="opencode=OPENCODE_API_KEY anthropic=ANTHROPIC_API_KEY"

opencode_instalar() {
  local versao=${PLAB_OPENCODE:?PLAB_OPENCODE nao definido}
  if [ "$(npm ls -g --prefix "$NPM_PREFIXO" --depth 0 --json 2>/dev/null | jq -r --arg p "$OPENCODE_PACOTE" '.dependencies[$p].version // empty')" = "$versao" ]; then
    echo "  opencode: ${OPENCODE_PACOTE}@${versao} ja instalado"
  else
    npm install -g --prefix "$NPM_PREFIXO" --no-audit --no-fund "${OPENCODE_PACOTE}@${versao}" >/dev/null || return 1
    echo "  opencode: ${OPENCODE_PACOTE}@${versao} instalado"
  fi
  # Wrapper: carrega SO a variavel escolhida no setup (gravada sem valor em state.json) e trava a versao.
  mkdir -p "${HOME}/.local/bin"
  cat > "${HOME}/.local/bin/opencode" <<EOF
#!/usr/bin/env bash
# gerado por lab setup: carrega apenas a chave do opencode escolhida no setup, se existir
v=\$(jq -r '.ias.opencode.chave // empty' "\$HOME/.config/lab/state.json" 2>/dev/null)
case "\$v" in
  OPENCODE_API_KEY|ANTHROPIC_API_KEY)
    if grep -q "^\${v}=" "\$HOME/.config/lab/secrets.env" 2>/dev/null; then
      export "\${v}=\$(set -a; . "\$HOME/.config/lab/secrets.env"; printf '%s' "\${!v}")"
    fi ;;
esac
unset v
export OPENCODE_DISABLE_AUTOUPDATE=1
exec "${NPM_PREFIXO}/bin/opencode" "\$@"
EOF
  chmod 755 "${HOME}/.local/bin/opencode"
}

opencode_autenticar() { # modo: conta|api_key ; interativo: 1|0
  local modo=$1 interativo=$2 prov var par
  case "$modo" in
    api_key)
      var=$(estado_get '.ias.opencode.chave')
      if [ -n "$var" ] && segredo_existe "$var"; then
        if [ "$interativo" = 1 ]; then
          read -r -p "  opencode: ja existe chave ($var); substituir? [s/N] " r; [ "$r" = s ] || return 0
        else return 0; fi
      fi
      [ "$interativo" = 1 ] || { return 2; }
      read -r -p "  opencode: provedor da chave [opencode/anthropic] (opencode): " prov
      prov=${prov:-opencode}; var=""
      for par in $OPENCODE_CHAVES; do [ "${par%%=*}" = "$prov" ] && var=${par#*=}; done
      [ -n "$var" ] || { echo "  opencode: provedor nao suportado: $prov"; return 1; }
      segredo_ler "$var" "  $var" || return 2
      estado_set '.ias.opencode.chave' "$var" ;;
    conta)
      # Conta nao usa chave do secrets.env: o wrapper deixa de carregar qualquer variavel.
      estado_set '.ias.opencode.chave' ""
      if [ -s "$OPENCODE_AUTH" ]; then
        chmod 600 "$OPENCODE_AUTH"
        if [ "$interativo" = 1 ]; then
          read -r -p "  opencode: ja existe login ($OPENCODE_AUTH); refazer? [s/N] " r; [ "$r" = s ] || return 0
        else return 0; fi
      fi
      [ "$interativo" = 1 ] || { return 2; }
      echo "  opencode: escolha o provedor e o metodo. No container prefira metodos com codigo de"
      echo "            dispositivo ou chave colada (ex.: GitHub Copilot, OpenCode); metodos que abrem"
      echo "            navegador local podem nao concluir aqui."
      "${HOME}/.local/bin/opencode" auth login || return 1
      [ -f "$OPENCODE_AUTH" ] && chmod 600 "$OPENCODE_AUTH" ;;
  esac
  return 0
}

opencode_testar() {
  local saida
  saida=$(timeout 180 "${HOME}/.local/bin/opencode" run "Responda apenas: OK" 2>&1) || { echo "falhou: ${saida:0:160}"; return 1; }
  grep -q 'OK' <<<"$saida" || { echo "resposta inesperada: ${saida:0:160}"; return 1; }
}

opencode_dir_skills() { echo "$OPENCODE_DIR_SKILLS"; }
