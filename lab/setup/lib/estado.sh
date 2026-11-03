#!/usr/bin/env bash
# Estado do "lab setup" (sem segredo) em ~/.config/lab/state.json, para idempotencia.
LAB_CFG="${HOME}/.config/lab"
LAB_ESTADO="${LAB_CFG}/state.json"

estado_iniciar() {
  mkdir -p "$LAB_CFG" && chmod 700 "$LAB_CFG"
  [ -s "$LAB_ESTADO" ] || echo '{"ias":{},"skills":{},"workspace":{}}' > "$LAB_ESTADO"
}

# Versoes anteriores gravavam ate 160 caracteres da saida da CLI em "falhou(teste: ...)", e
# algumas CLIs ecoam parte mascarada da chave. Fica so a categoria.
estado_sanear() {
  grep -q 'falhou(teste: ' "$LAB_ESTADO" 2>/dev/null || return 0
  estado_jq '(.ias[]?.estado | select(type == "string" and startswith("falhou(teste:"))) |= "falhou(teste)"'
}

# estado_jq <filtro jq> [argumentos do jq] - aplica o filtro e regrava o state.json.
estado_jq() {
  local filtro=$1 tmp; shift
  tmp=$(mktemp)
  jq "$@" "$filtro" "$LAB_ESTADO" > "$tmp" && mv "$tmp" "$LAB_ESTADO"
}

# estado_set <caminho jq> <valor string>
estado_set() { estado_jq "$1 = \$v" --arg v "$2"; }

# estado_get <caminho jq>
estado_get() { jq -r "$1 // empty" "$LAB_ESTADO" 2>/dev/null; }
