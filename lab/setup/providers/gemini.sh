#!/usr/bin/env bash
# Provider Gemini CLI para o "lab setup".
# Fontes (consultadas em 02/11/2026; ver research.md R-07): geminicli.com/docs get-started/
# authentication, cli/headless, cli/skills, cli/gemini-md, reference/configuration (lidas no
# repositorio oficial google-gemini/gemini-cli, pasta docs).
#  - pacote npm @google/gemini-cli; general.enableAutoUpdate=false em ~/.gemini/settings.json;
#  - conta ("Login with Google", authType oauth-personal): com NO_BROWSER=true o CLI interativo mostra
#    "Please visit the following URL to authorize the application", o Google exibe um codigo em
#    codeassist.google.com/authcode e o CLI pede "Enter the authorization code" (verificado no
#    0.66.0 em 03/11/2026; com -p o login manual e recusado). Credencial em ~/.gemini/oauth_creds.json;
#  - chave: GEMINI_API_KEY (Google AI Studio), lida so por variavel de ambiente (sem login por
#    stdin) -> carregada so pelo wrapper, a partir de ~/.config/lab/secrets.env;
#  - skills em ~/.gemini/skills/<nome>/SKILL.md (alias ~/.agents/skills); instrucoes: GEMINI.md.

GEMINI_PACOTE="@google/gemini-cli"
GEMINI_DIR_SKILLS="${HOME}/.gemini/skills"
GEMINI_SETTINGS="${HOME}/.gemini/settings.json"

gemini_modos() { echo "conta api_key"; }
GEMINI_OAUTH="${HOME}/.gemini/oauth_creds.json"

# Grava o tipo de autenticacao no settings.json do Gemini, preservando o resto.
gemini_tipo_auth() { # oauth-personal | gemini-api-key
  local tmp base='{}'; tmp=$(mktemp)
  [ -s "$GEMINI_SETTINGS" ] && base=$(cat "$GEMINI_SETTINGS")
  jq --arg t "$1" '.security.auth.selectedType = $t' <<<"$base" > "$tmp" && cp "$tmp" "$GEMINI_SETTINGS"
  rm -f "$tmp"
}

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
# gerado por lab setup: carrega apenas GEMINI_API_KEY de ~/.config/lab/secrets.env, e so no modo
# api_key (no modo conta vale o login Google em ~/.gemini/oauth_creds.json)
modo=\$(jq -r '.ias.gemini.auth // empty' "\$HOME/.config/lab/state.json" 2>/dev/null)
if [ "\$modo" = api_key ] && grep -q '^GEMINI_API_KEY=' "\$HOME/.config/lab/secrets.env" 2>/dev/null; then
  export GEMINI_API_KEY="\$(set -a; . "\$HOME/.config/lab/secrets.env"; printf '%s' "\$GEMINI_API_KEY")"
fi
unset modo
exec "${NPM_PREFIXO}/bin/gemini" "\$@"
EOF
  chmod 755 "${HOME}/.local/bin/gemini"
}

# Login de conta conduzido pelo setup. O Gemini mostra a URL numa "tela alternativa" do terminal e,
# se o login nao conclui, volta para a tela de chave de API e grava selectedType=gemini-api-key
# (visto em 03/11/2026 num terminal Windows). Aqui ele roda num terminal interno (script): o setup
# mostra a URL na tela normal, le o codigo e o repassa; ao gravar oauth_creds.json, fecha o Gemini.
gemini_login_conta() {
  local d pid url codigo _
  d=$(mktemp -d /tmp/plab-gemini.XXXXXX); chmod 700 "$d"; mkfifo "$d/in"
  ( cd /workspace 2>/dev/null || cd "$HOME" || exit 1
    NO_BROWSER=true exec script -qfec "${NPM_PREFIXO}/bin/gemini" "$d/out" < "$d/in" > /dev/null 2>&1 ) &
  pid=$!
  exec 7> "$d/in"
  url=""
  for _ in $(seq 1 60); do
    url=$(sed -E 's/\x1b\[[0-9;?]*[a-zA-Z]//g' "$d/out" 2>/dev/null | tr '\r\n' '  ' \
          | grep -aoE 'https://accounts\.google\.com/o/oauth2/v2/auth[^[:space:]]+' | head -n 1)
    [ -n "$url" ] && break
    sleep 1
  done
  if [ -z "$url" ]; then
    echo "  gemini: a URL de login nao apareceu em 60 s"
  else
    echo
    echo "  1. Abra esta URL no navegador do seu computador (copie a linha inteira):"
    echo
    echo "$url"
    echo
    echo "  2. Entre com sua conta Google e autorize; o Google mostra um codigo."
    IFS= read -r -p "  3. Cole o codigo aqui e tecle Enter: " codigo
    printf '%s\r' "$codigo" >&7
    unset codigo
    for _ in $(seq 1 60); do [ -s "$GEMINI_OAUTH" ] && break; sleep 1; done
  fi
  printf '/quit\r' >&7 2>/dev/null; sleep 3
  exec 7>&-
  kill "$pid" 2>/dev/null; pkill -f "${NPM_PREFIXO}/bin/gemini" 2>/dev/null; wait "$pid" 2>/dev/null
  if [ ! -s "$GEMINI_OAUTH" ] && [ -s "$d/out" ]; then
    # Mensagens de erro do proprio Gemini, para diagnostico. Saneadas: sem a linha do codigo e com
    # qualquer sequencia longa (token, codigo, URL) trocada por <omitido>.
    echo "  gemini: mensagens do Gemini sobre a falha:"
    sed -E 's/\x1b\[[0-9;?]*[a-zA-Z]//g; s/\x1b\][^\a]*\a//g' "$d/out" | tr -d '\r' \
      | grep -aiE 'error|erro|fail|falh|denied|permission|project|not supported|unsupported|eligib|quota|region' \
      | grep -avi 'Enter the authorization code' \
      | sed -E 's#[A-Za-z0-9_./~+=%-]{25,}#<omitido>#g' | sort -u | head -n 12 | sed 's/^/    /'
  fi
  rm -rf "$d"  # o registro do terminal interno tem o codigo digitado
  gemini_tipo_auth oauth-personal  # o Gemini troca para chave quando o login falha
  if [ -s "$GEMINI_OAUTH" ]; then chmod 600 "$GEMINI_OAUTH"; echo "  gemini: login Google concluido"; return 0; fi
  echo "  gemini: login nao concluido (sem $GEMINI_OAUTH)"; return 1
}

gemini_autenticar() { # modo: conta|api_key ; interativo: 1|0
  local modo=$1 interativo=$2
  case "$modo" in
    conta)
      gemini_tipo_auth oauth-personal
      if [ -s "$GEMINI_OAUTH" ]; then
        chmod 600 "$GEMINI_OAUTH"
        if [ "$interativo" = 1 ]; then
          read -r -p "  gemini: ja existe login Google; refazer? [s/N] " r; [ "$r" = s ] || return 0
          rm -f "$GEMINI_OAUTH"
        else return 0; fi
      fi
      [ "$interativo" = 1 ] || return 2
      gemini_login_conta || return 2
      chmod 600 "$GEMINI_OAUTH" ;;
    api_key)
      gemini_tipo_auth gemini-api-key
      if segredo_existe GEMINI_API_KEY && [ "$interativo" = 1 ]; then
        read -r -p "  ja existe chave do Gemini; substituir? [s/N] " r; [ "$r" = s ] || return 0
      elif segredo_existe GEMINI_API_KEY; then return 0; fi
      [ "$interativo" = 1 ] || { return 2; }
      echo "  gemini: crie a chave em https://aistudio.google.com/app/apikey"
      segredo_ler GEMINI_API_KEY "  GEMINI_API_KEY" || return 2 ;;
  esac
}

gemini_testar() {
  local saida
  saida=$(timeout 180 "${HOME}/.local/bin/gemini" --skip-trust -p "Responda apenas: OK" 2>&1) || { echo "falhou: ${saida:0:160}"; return 1; }
  grep -q 'OK' <<<"$saida" || { echo "resposta inesperada: ${saida:0:160}"; return 1; }
}

gemini_dir_skills() { echo "$GEMINI_DIR_SKILLS"; }
