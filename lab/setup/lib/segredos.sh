#!/usr/bin/env bash
# Segredos do "lab setup": lidos sem eco e gravados so em ~/.config/lab/secrets.env (0600).
# Nunca recebem segredo por argumento, nunca ecoam, nunca duplicam a variavel.
LAB_SEGREDOS="${HOME}/.config/lab/secrets.env"

segredos_preparar() {
  mkdir -p "$(dirname "$LAB_SEGREDOS")"
  [ -f "$LAB_SEGREDOS" ] || : > "$LAB_SEGREDOS"
  chmod 600 "$LAB_SEGREDOS"
}

segredo_existe() { grep -q "^$1=" "$LAB_SEGREDOS" 2>/dev/null; }

# segredo_ler <VARIAVEL> <rotulo> - le com read -s; recusa vazio; substitui sem duplicar.
segredo_ler() {
  local var=$1 rotulo=$2 valor=""
  segredos_preparar
  while [ -z "$valor" ]; do
    IFS= read -r -s -p "$rotulo (nao aparece na tela; Enter vazio cancela): " valor || return 1
    echo
    [ -n "$valor" ] || { echo "nada informado; cancelado."; return 1; }
  done
  local tmp; tmp=$(mktemp); chmod 600 "$tmp"
  grep -v "^${var}=" "$LAB_SEGREDOS" > "$tmp" || true
  printf '%s=%q\n' "$var" "$valor" >> "$tmp"
  mv "$tmp" "$LAB_SEGREDOS"; chmod 600 "$LAB_SEGREDOS"
  unset valor
}

# segredo_valor <VARIAVEL> - imprime o valor (para pipe direto ao comando que o consome).
segredo_valor() {
  # shellcheck source=/dev/null  # arquivo do usuario, gerado por segredo_ler
  ( set -a; . "$LAB_SEGREDOS"; set +a; printf '%s' "${!1:-}" )
}
