#!/usr/bin/env bash
# Provider Gemini CLI para o "lab setup".
# Fontes (consultadas em 02/11/2026; ver research.md R-07): geminicli.com/docs get-started/
# authentication, cli/headless, cli/skills, cli/gemini-md, reference/configuration (lidas no
# repositorio oficial google-gemini/gemini-cli, pasta docs).
#  - pacote npm @google/gemini-cli; general.enableAutoUpdate=false em ~/.gemini/settings.json;
#  - conta ("Sign in with Google"): exige navegador numa maquina que alcance o terminal; a doc nao
#    descreve fluxo por codigo de dispositivo ou URL copiavel -> NAO oferecido no lab;
#  - chave: GEMINI_API_KEY (Google AI Studio), lida so por variavel de ambiente (sem login por
#    stdin) -> carregada so pelo wrapper, a partir de ~/.config/lab/secrets.env;
#  - skills em ~/.gemini/skills/<nome>/SKILL.md (alias ~/.agents/skills); instrucoes: GEMINI.md.

GEMINI_PACOTE="@google/gemini-cli"
GEMINI_DIR_SKILLS="${HOME}/.gemini/skills"
GEMINI_SETTINGS="${HOME}/.gemini/settings.json"

gemini_modos() { echo "api_key"; }

gemini_instalar() {
  local versao=${PLAB_GEMINI_CLI:?PLAB_GEMINI_CLI nao definido}
  if [ "$(npm ls -g --prefix "$NPM_PREFIXO" --depth 0 --json 2>/dev/null | jq -r --arg p "$GEMINI_PACOTE" '.dependencies[$p].version // empty')" = "$versao" ]; then
    echo "  gemini: ${GEMINI_PACOTE}@${versao} ja instalado"
  else
    npm install -g --prefix "$NPM_PREFIXO" --no-audit --no-fund "${GEMINI_PACOTE}@${versao}" >/dev/null || return 1
    echo "  gemini: ${GEMINI_PACOTE}@${versao} instalado"
  fi
  # Mantem a versao fixada: desliga a atualizacao automatica, preservando o resto do settings.json.
  mkdir -p "$(dirname "$GEMINI_SETTINGS")"
  local tmp base='{}'; tmp=$(mktemp)
  [ -s "$GEMINI_SETTINGS" ] && base=$(cat "$GEMINI_SETTINGS")
  if jq '.general.enableAutoUpdate = false | .general.enableAutoUpdateNotification = false' <<<"$base" > "$tmp"; then
    cmp -s "$tmp" "$GEMINI_SETTINGS" 2>/dev/null || cp "$tmp" "$GEMINI_SETTINGS"
  else
    echo "  gemini: aviso: $GEMINI_SETTINGS nao e JSON valido; atualizacao automatica nao desligada" >&2
  fi
  rm -f "$tmp"
  # Wrapper: carrega SO a GEMINI_API_KEY e chama o binario real.
  mkdir -p "${HOME}/.local/bin"
  cat > "${HOME}/.local/bin/gemini" <<EOF
#!/usr/bin/env bash
# gerado por lab setup: carrega apenas GEMINI_API_KEY de ~/.config/lab/secrets.env, se existir
if grep -q '^GEMINI_API_KEY=' "\$HOME/.config/lab/secrets.env" 2>/dev/null; then
  export GEMINI_API_KEY="\$(set -a; . "\$HOME/.config/lab/secrets.env"; printf '%s' "\$GEMINI_API_KEY")"
fi
exec "${NPM_PREFIXO}/bin/gemini" "\$@"
EOF
  chmod 755 "${HOME}/.local/bin/gemini"
}

gemini_autenticar() { # modo: api_key (conta nao suportado) ; interativo: 1|0
  local modo=$1 interativo=$2
  [ "$modo" = api_key ] || { echo "  gemini: modo $modo nao suportado no lab (use api_key)"; return 1; }
  if segredo_existe GEMINI_API_KEY && [ "$interativo" = 1 ]; then
    read -r -p "  ja existe chave do Gemini; substituir? [s/N] " r; [ "$r" = s ] || return 0
  elif segredo_existe GEMINI_API_KEY; then return 0; fi
  [ "$interativo" = 1 ] || { return 2; }
  echo "  gemini: crie a chave em https://aistudio.google.com/app/apikey"
  segredo_ler GEMINI_API_KEY "  GEMINI_API_KEY" || return 2
}

gemini_testar() {
  local saida
  saida=$(timeout 180 "${HOME}/.local/bin/gemini" --skip-trust -p "Responda apenas: OK" 2>&1) || { echo "falhou: ${saida:0:160}"; return 1; }
  grep -q 'OK' <<<"$saida" || { echo "resposta inesperada: ${saida:0:160}"; return 1; }
}

gemini_dir_skills() { echo "$GEMINI_DIR_SKILLS"; }
