#!/usr/bin/env bash
# Estado do "lab setup" (sem segredo) em ~/.config/lab/state.json, para idempotencia.
LAB_CFG="${HOME}/.config/lab"
LAB_ESTADO="${LAB_CFG}/state.json"

estado_iniciar() {
  mkdir -p "$LAB_CFG" && chmod 700 "$LAB_CFG"
  [ -s "$LAB_ESTADO" ] || echo '{"ias":{},"skills":{},"workspace":{}}' > "$LAB_ESTADO"
}

# estado_set <caminho jq> <valor string>
estado_set() {
  local tmp; tmp=$(mktemp)
  jq --arg v "$2" "$1 = \$v" "$LAB_ESTADO" > "$tmp" && mv "$tmp" "$LAB_ESTADO"
}

# estado_get <caminho jq>
estado_get() { jq -r "$1 // empty" "$LAB_ESTADO" 2>/dev/null; }
