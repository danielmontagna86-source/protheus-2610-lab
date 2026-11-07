#!/bin/bash
# appserver-reserva.sh - entrada do AppServer da fonte reserva (imagens feliperaposo/*).
# Ajusta o appserver.ini da imagem e passa para o /protheus.sh original da imagem.
# Roda a cada start; cada ajuste e idempotente (o .ini fica na camada do container).
#
#  1. Nomes exclusivos para DBAccess e License Server. O .ini da imagem usa "dbaccess" e
#     "license-server"; na rede plab o Docker tambem resolve "dbaccess" para os DBAccess das stacks
#     principais (o nome do servico vira alias em todas as redes). Em 05/11/2026 um AppServer da
#     reserva ligado a plab abriu conexoes no DBAccess da 2510 principal por isso.
#  2. Ambiente com o nome que o lab usa (PLAB_<rel>_ENV), no lugar do P12 da imagem.
#  3. Ambiente de compilacao (PLAB_<rel>_ENV_COMPILA) com RPO proprio, semeado pelo rpo-init,
#     para a compilacao do smoke nao tocar no RPO do ambiente principal (mesmo modelo da stack
#     principal).
set -euo pipefail

ini=/protheus12/bin/appserver/appserver.ini
amb=${PLAB_RES_ENV:?defina PLAB_RES_ENV}
comp=${PLAB_RES_ENV_COMPILA:?defina PLAB_RES_ENV_COMPILA}

sed -i -e '/^\[DBAccess\]/,/^\[/ s/^Server=.*/Server=dbaccess-res/' \
       -e '/^\[LicenseClient\]/,/^\[/ s/^Server=.*/Server=license-res/' "$ini"

sed -i -E -e "s/^\[P12\]\r?$/[$amb]/" -e "s/=P12(\r?)$/=$amb\1/" "$ini"

if ! grep -q "^\[$comp\]" "$ini"; then
  # Le a secao inteira antes de gravar (nao ler e acrescentar o mesmo arquivo no mesmo pipeline).
  secao=$(sed -n "/^\[$amb\]/,/^\[/p" "$ini" | sed -e '1d' -e '/^\[/d' -e '/^\s*$/d' \
    | sed -E -e 's#^SourcePath=.*#SourcePath=/protheus12/apo_compila#' \
             -e 's#^RPOCustom=.*#RPOCustom=/protheus12/apo_compila/custom.rpo#')
  printf '\n[%s]\n%s\n' "$comp" "$secao" >> "$ini"
fi

# 3b. /app-root (tela de login da interface nova) pelo HTTPSERVER da 9995, com o AppServer na 1235;
#     a porta 1234 fica com o HAProxy do servico "approot" do compose, que divide a porta
#     (stacks/reserva/haproxy-approot.cfg). E o esquema que a imagem 2610 ja traz, sem o
#     app-root-proxy do autor: ele deixava conexoes presas em CLOSE_WAIT e degradava o AppServer
#     depois de umas 25 sessoes (06/11/2026). O proxy da imagem perde o bit de execucao para o
#     /protheus.sh nao inicia-lo. O /app-root nativo da porta multiprotocolo nao serve: na 2510 falha
#     ("REST could not be initialized!"); na 2610, em base nova, derruba o AppServer ("FAILURE TO
#     START REST SERVER") ou, com a secao [MPP_CLima] da imagem (mantida), nao responde.
[ -x /usr/local/bin/app-root-proxy ] && chmod -x /usr/local/bin/app-root-proxy
sed -i -e '/^\[TCP\]/,/^\[/ s/^Port=.*/Port=1235/' "$ini"
if ! grep -q '^\[APP_ROOT\]' "$ini"; then
  printf '\n[HTTPSERVER]\nEnable=1\nServers=HTTPAPP\n\n[HTTPAPP]\nHostname=localhost\nPort=9995\nLocations=APP_ROOT\n\n[APP_ROOT]\nPath=/app-root\nRootPath=/protheus12/protheus_data/http-root/app-root\nThreadPool=APP_POOL\n\n[APP_POOL]\nEnvironment=%s\nMinThreads=1\nSlaves=APP_SLAVES\n\n[APP_SLAVES]\nEnvironment=%s\nMinThreads=1\n' \
    "$amb" "$amb" >> "$ini"
fi
# Depois do plab inicializar (marca no volume da reserva) e so onde PLAB_RES_APPROOT_NATIVO=sim
# (2610): /app-root nativo da porta multiprotocolo (1235, atras do HAProxy), sem o HTTPSERVER. Com o
# /app-root no HTTPSERVER, o aviso da issue #21 apareceu em 3 a 6 de 8 logins na 2610; nativo, em
# 1 de 8. O nativo so funciona em base ja inicializada, e precisa sem a secao [MPP_CLima].
marca=/protheus12/apo_compila/.plab-base-inicializada
if [ "${PLAB_RES_APPROOT_NATIVO:-nao}" = sim ] && [ -f "$marca" ]; then
  sed -i -e '/^\[MPP_CLima\]/,/^\[/{/^\[MPP_CLima\]/d;/^NewRestOn/d}' \
         -e '/^\[HTTPSERVER\]/,/^\[/ s/^Enable=1/Enable=0/' "$ini"
else
  sed -i -e '/^\[HTTPSERVER\]/,/^\[/ s/^Enable=0/Enable=1/' "$ini"
fi

# 4. REST na porta interna que o lab usa (8181, como na principal; a imagem traz 8080).
sed -i -e '/^\[HTTPREST\]/,/^\[/ s/^Port=.*/Port=8181/' "$ini"

# 5. /app-root/ (a pagina que o lab doctor confere) responde 200: o HTTPSERVER do
#    /app-root (secao [APP_ROOT]) sem pagina padrao responde 406 "the parameter default page is
#    missing" na raiz.
if grep -q '^\[APP_ROOT\]' "$ini"; then
  grep -q '^DefaultPage=' "$ini" || sed -i '/^\[APP_ROOT\]/a DefaultPage=index.html' "$ini"
  raiz_app=/protheus12/protheus_data/http-root/app-root
  mkdir -p "$raiz_app"
  [ -f "$raiz_app/index.html" ] || printf '<!doctype html><title>app-root</title>\n' > "$raiz_app/index.html"
fi

export DBAPI_URL=http://dbaccess-res:7891/dbapi.so
exec /protheus.sh
