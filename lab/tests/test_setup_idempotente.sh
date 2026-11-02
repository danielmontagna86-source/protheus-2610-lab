#!/usr/bin/env bash
# Idempotencia do "lab setup" (FR-013 / SC-004): duas execucoes nao interativas seguidas precisam
# deixar o mesmo estado, os mesmos arquivos de instrucoes e as mesmas skills, sem duplicar nada.
# Roda dentro do container lab. Nao exige credencial (modo conta sem interacao = nao_testado;
# Gemini so tem api_key, entao em modo conta fica nao_suportado, o que tambem precisa ser estavel).
#   test_setup_idempotente.sh [release] [ias]   ex.: 2610 claude,codex,opencode,gemini
set -uo pipefail
rel=${1:-2610}
ias=${2:-claude,codex}
dirs=()
for ia in ${ias//,/ }; do
  case "$ia" in
    claude) dirs+=("$HOME/.claude/skills") ;;
    codex) dirs+=("$HOME/.codex/skills") ;;
    opencode) dirs+=("$HOME/.config/opencode/skills") ;;
    gemini) dirs+=("$HOME/.gemini/skills") ;;
  esac
done
foto() {
  {
    jq -S . "$HOME/.config/lab/state.json"
    for f in /workspace/AGENTS.md /workspace/CLAUDE.md /workspace/GEMINI.md; do sha256sum "$f"; done
    for d in "${dirs[@]}"; do
      [ -d "$d" ] || { echo "$d: ausente"; continue; }
      echo "$d: $(find "$d" -type f | wc -l) arquivos $(find "$d" -type f -exec sha256sum {} + | sort | sha256sum | cut -c1-16)"
    done
    echo "linhas secrets.env: $(wc -l < "$HOME/.config/lab/secrets.env")"
    stat -c '%a %n' "$HOME/.config/lab/secrets.env"
  }
}
lab setup --release "$rel" --ia "$ias" --auth conta --nao-interativo --sem-smoke > /tmp/setup1.log 2>&1 || { echo "FALHA execucao 1"; tail -20 /tmp/setup1.log; exit 1; }
foto > /tmp/foto1
lab setup --release "$rel" --ia "$ias" --auth conta --nao-interativo --sem-smoke > /tmp/setup2.log 2>&1 || { echo "FALHA execucao 2"; tail -20 /tmp/setup2.log; exit 1; }
foto > /tmp/foto2
if diff -u /tmp/foto1 /tmp/foto2; then
  echo "idempotente: OK"; cat /tmp/foto2
else
  echo "idempotente: FALHOU"; exit 1
fi
grep -q '^600 ' <(stat -c '%a %n' "$HOME/.config/lab/secrets.env") || { echo "secrets.env sem modo 600"; exit 1; }
echo "secrets.env 600: OK"
