#!/usr/bin/env bash
# lab doctor <release> - diagnostico da release pela rede plab.
# Sai no primeiro item que falhar, nomeando-o (FR-008). Codigos: 31 DNS, 32 TCP AppServer,
# 33 WebApp, 34 /app-root, 35 REST, 36 License Server, 37 DBAccess, 38 secret.
set -uo pipefail
. "${PLAB_HOME:-/opt/plab}/lab/bin/lib/comum.sh"

rel=${1:-}
validar_release "$rel" || exit 2
host=$(host_release "$rel")

passo() { printf '  %-28s ' "$1"; }

# Codigo HTTP com novas tentativas: logo apos uma compilacao o AppServer reinicia os servidores
# HTTP por alguns segundos (2610: ~12 s). Espera ate PLAB_DOCTOR_ESPERA segundos (padrao 60).
http_codigo() {
  local url=$1 cod fim=$((SECONDS + ${PLAB_DOCTOR_ESPERA:-60}))
  while :; do
    cod=$(curl -s -o /dev/null -w '%{http_code}' -m 10 "$url")
    [ "$cod" = 200 ] || [ $SECONDS -ge $fim ] && { echo "$cod"; return; }
    sleep 5
  done
}
ok() { echo "OK${1:+  ($1)}"; }
falha() { echo "FALHOU  ($1)"; exit "${2:-1}"; }

echo "doctor $rel"

passo "DNS $host"
ip=$(getent hosts "$host" | awk '{print $1}' | head -n 1)
[ -n "$ip" ] || falha "nome nao resolve: a stack $rel esta de pe? rode no host: plab up $rel" 31
ok "$ip"

passo "TCP $host:$PLAB_PORT_TCP_INTERNA"
(exec 3<>"/dev/tcp/$host/$PLAB_PORT_TCP_INTERNA") 2>/dev/null || falha "porta fechada: appserver parado ou iniciando" 32
ok

passo "WebApp /webapp/"
cod=$(http_codigo "$(url_webapp "$rel")")
[ "$cod" = 200 ] || falha "HTTP $cod" 33
ok "HTTP 200"

passo "Login PO UI /app-root/"
cod=$(http_codigo "http://$host:$PLAB_PORT_TCP_INTERNA/app-root/")
[ "$cod" = 200 ] || falha "HTTP $cod (interface nova indisponivel)" 34
ok "HTTP 200"

passo "REST /rest/"
cod=$(http_codigo "http://$host:$PLAB_PORT_REST_INTERNA/rest/")
[ "$cod" = 200 ] || falha "HTTP $cod" 35
ok "HTTP 200"

# License Server e DBAccess: aliases na rede plab (stacks/<rel>/compose.yaml). Sem eles o AppServer
# ate responde HTTP, mas login e rotinas falham.
tcp_servico() { # rotulo host porta codigo dica
  passo "$1 $2:$3"
  (exec 3<>"/dev/tcp/$2/$3") 2>/dev/null || falha "porta fechada: $5" "$4"
  ok
}
tcp_servico "License Server" "license-server-$rel" 5555 36 "License Server parado; veja: plab logs $rel license"
tcp_servico "DBAccess" "dbaccess-$rel" 7890 37 "DBAccess parado ou sem banco; veja: plab logs $rel dbaccess"

passo "Senha Admin (secret)"
senha_admin "$rel" >/dev/null 2>&1 || falha "secret vazio: preencha PLAB_${rel}_ADMIN_PASSWORD no .env" 38
ok "presente"

echo "doctor $rel: OK"
