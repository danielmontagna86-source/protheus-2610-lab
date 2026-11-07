#!/usr/bin/env bash
# Funcoes comuns dos comandos "lab". Carregado com ". comum.sh".

# Portas internas fixas das imagens (dentro da rede plab). Usadas pelos scripts que carregam este.
# shellcheck disable=SC2034
PLAB_PORT_TCP_INTERNA=1234
PLAB_PORT_REST_INTERNA=8181

erro() { echo "lab: $*" >&2; }

validar_release() {
  case "${1:-}" in
    2610|2510) return 0 ;;
    *) erro "release invalida: '${1:-}' (use 2610 ou 2510)"; return 2 ;;
  esac
}

# Variavel indireta: valor_release 2610 HOST -> $PLAB_2610_HOST
valor_release() { local v="PLAB_${1}_${2}"; printf '%s' "${!v:-}"; }

host_release() { valor_release "$1" HOST; }

url_webapp() { printf 'http://%s:%s/webapp/' "$(host_release "$1")" "$PLAB_PORT_TCP_INTERNA"; }

# Senha do Admin: lida do secret montado pelo compose, nunca de argumento.
# Imprime em stdout para ser capturada em variavel; nunca registrar em log.
# PLAB_SECRETS_DIR existe so para os testes locais (lab/tests); no lab e sempre /run/secrets.
senha_admin() {
  local arq="${PLAB_SECRETS_DIR:-/run/secrets}/plab_${1}_admin_password"
  if [ -r "$arq" ] && [ -s "$arq" ]; then tr -d '\r\n' < "$arq"; return 0; fi
  erro "senha do Admin da $1 ausente: preencha PLAB_${1}_ADMIN_PASSWORD no .env do host e recrie o lab"
  return 3
}

carimbo() { date +%Y%m%d-%H%M%S; }

# A release esta na fonte reserva (base vazia)? O appserver da reserva publica tambem o alias
# appserver-<rel>-reserva na rede plab (stacks/reserva/<rel>/compose.yaml); a principal nao.
fonte_reserva() { getent hosts "appserver-$1-reserva" >/dev/null 2>&1; }
