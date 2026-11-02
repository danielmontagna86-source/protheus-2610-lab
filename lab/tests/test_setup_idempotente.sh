#!/usr/bin/env bash
# Idempotencia do "lab setup" (FR-013 / SC-004): duas execucoes nao interativas seguidas precisam
# deixar o mesmo estado, os mesmos arquivos de instrucoes e as mesmas skills, sem duplicar nada.
# Roda dentro do container lab. Nao exige credencial (modo conta sem interacao = nao_testado).
set -uo pipefail
rel=${1:-2610}
foto() {
  {
    jq -S . "$HOME/.config/lab/state.json"
    for f in /workspace/AGENTS.md /workspace/CLAUDE.md /workspace/GEMINI.md; do sha256sum "$f"; done
    for d in "$HOME/.claude/skills" "$HOME/.codex/skills"; do
      echo "$d: $(find "$d" -type f | wc -l) arquivos $(find "$d" -type f -exec sha256sum {} + | sort | sha256sum | cut -c1-16)"
    done
    echo "linhas secrets.env: $(wc -l < "$HOME/.config/lab/secrets.env")"
    stat -c '%a %n' "$HOME/.config/lab/secrets.env"
  }
}
lab setup --release "$rel" --ia claude,codex --auth conta --nao-interativo --sem-smoke > /tmp/setup1.log 2>&1 || { echo "FALHA execucao 1"; tail -20 /tmp/setup1.log; exit 1; }
foto > /tmp/foto1
lab setup --release "$rel" --ia claude,codex --auth conta --nao-interativo --sem-smoke > /tmp/setup2.log 2>&1 || { echo "FALHA execucao 2"; tail -20 /tmp/setup2.log; exit 1; }
foto > /tmp/foto2
if diff -u /tmp/foto1 /tmp/foto2; then
  echo "idempotente: OK"; cat /tmp/foto2
else
  echo "idempotente: FALHOU"; exit 1
fi
grep -q '^600 ' <(stat -c '%a %n' "$HOME/.config/lab/secrets.env") || { echo "secrets.env sem modo 600"; exit 1; }
echo "secrets.env 600: OK"
