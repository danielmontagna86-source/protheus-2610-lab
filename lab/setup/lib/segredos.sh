#!/usr/bin/env bash
# Segredos do "lab setup": lidos sem eco e gravados so em ~/.config/lab/secrets.env (0600).
# Nunca recebem segredo por argumento, nunca ecoam, nunca duplicam a variavel.
LAB_SEGREDOS="${HOME}/.config/lab/secrets.env"

segredos_preparar() {
  local dir; dir=$(dirname "$LAB_SEGREDOS")
  # 700 aqui mesmo: nao depende de estado_iniciar ter rodado antes.
  mkdir -p "$dir" && chmod 700 "$dir"
  [ -f "$LAB_SEGREDOS" ] || ( umask 077; : > "$LAB_SEGREDOS" )
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
  # Temporario no mesmo diretorio (volume lab-home): o mv vira um rename atomico, e uma falha nao
  # deixa copia dos segredos na camada do container (/tmp).
  local tmp
  tmp=$(mktemp "$(dirname "$LAB_SEGREDOS")/.secrets.XXXXXX") || { unset valor; return 1; }
  chmod 600 "$tmp"
  if { grep -v "^${var}=" "$LAB_SEGREDOS" || true; } > "$tmp" \
     && printf '%s=%q\n' "$var" "$valor" >> "$tmp" \
     && mv -f "$tmp" "$LAB_SEGREDOS"; then
    chmod 600 "$LAB_SEGREDOS"
  else
    rm -f "$tmp"; unset valor; return 1
  fi
  unset valor
}

# segredo_valor <VARIAVEL> - imprime o valor (para pipe direto ao comando que o consome).
segredo_valor() {
  # shellcheck source=/dev/null  # arquivo do usuario, gerado por segredo_ler
  ( set -a; . "$LAB_SEGREDOS"; set +a; printf '%s' "${!1:-}" )
}
