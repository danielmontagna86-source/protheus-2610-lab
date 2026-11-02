#!/usr/bin/env bash
# Provider Codex CLI para o "lab setup".
# Fontes (consultadas em 02/11/2026): learn.chatgpt.com/docs/auth e developers.openai.com/codex/skills.
#  - pacote npm @openai/codex;
#  - conta: "codex login --device-auth" (codigo de dispositivo; precisa estar habilitado na conta);
#  - chave: "printenv OPENAI_API_KEY | codex login --with-api-key" (stdin, nunca argumento);
#  - credencial em ~/.codex/auth.json; skills em ~/.codex/skills/<nome>/SKILL.md.

CODEX_PACOTE="@openai/codex"
CODEX_DIR_SKILLS="${HOME}/.codex/skills"

codex_instalar() {
  local versao=${PLAB_CODEX:?PLAB_CODEX nao definido}
  if [ "$(npm ls -g --prefix "$NPM_PREFIXO" --depth 0 --json 2>/dev/null | jq -r --arg p "$CODEX_PACOTE" '.dependencies[$p].version // empty')" = "$versao" ]; then
    echo "  codex: ${CODEX_PACOTE}@${versao} ja instalado"
  else
    npm install -g --prefix "$NPM_PREFIXO" --no-audit --no-fund "${CODEX_PACOTE}@${versao}" >/dev/null || return 1
    echo "  codex: ${CODEX_PACOTE}@${versao} instalado"
  fi
  mkdir -p "${HOME}/.local/bin"
  ln -sf "${NPM_PREFIXO}/bin/codex" "${HOME}/.local/bin/codex"
}

codex_autenticar() { # modo: conta|api_key ; interativo: 1|0
  local modo=$1 interativo=$2
  if [ -s "${HOME}/.codex/auth.json" ]; then
    chmod 600 "${HOME}/.codex/auth.json"
    if [ "$interativo" = 1 ]; then
      read -r -p "  codex: ja existe login; refazer? [s/N] " r; [ "$r" = s ] || return 0
    else return 0; fi
  fi
  [ "$interativo" = 1 ] || { return 2; }
  case "$modo" in
    api_key)
      # A chave vai do secrets.env direto para o stdin do codex; nao fica em argumento nem no ambiente.
      segredo_ler OPENAI_API_KEY "  OPENAI_API_KEY" || return 2
      segredo_valor OPENAI_API_KEY | "${HOME}/.local/bin/codex" login --with-api-key || return 1 ;;
    conta)
      echo "  codex: abra o link mostrado e digite o codigo (device code precisa estar habilitado na conta)"
      "${HOME}/.local/bin/codex" login --device-auth || return 1 ;;
  esac
  [ -f "${HOME}/.codex/auth.json" ] && chmod 600 "${HOME}/.codex/auth.json"
  return 0
}

codex_testar() {
  local saida
  saida=$(timeout 180 "${HOME}/.local/bin/codex" exec --skip-git-repo-check "Responda apenas: OK" 2>&1) || { echo "falhou: ${saida:0:160}"; return 1; }
  grep -q 'OK' <<<"$saida" || { echo "resposta inesperada: ${saida:0:160}"; return 1; }
}

codex_dir_skills() { echo "$CODEX_DIR_SKILLS"; }
