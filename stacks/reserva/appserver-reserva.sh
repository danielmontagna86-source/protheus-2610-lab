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

# 4. REST na porta interna que o lab usa (8181, como na principal; a imagem traz 8080).
sed -i -e '/^\[HTTPREST\]/,/^\[/ s/^Port=.*/Port=8181/' "$ini"

# 5. /app-root/ (a pagina que o lab doctor confere) responde 200. Na 2610 desta imagem o /app-root
#    vem do HTTPSERVER interno (secao [APP_ROOT]) via proxy na 1234, e sem pagina padrao a raiz
#    responde 406 "the parameter default page is missing". A 2510 nao tem [APP_ROOT].
if grep -q '^\[APP_ROOT\]' "$ini"; then
  grep -q '^DefaultPage=' "$ini" || sed -i '/^\[APP_ROOT\]/a DefaultPage=index.html' "$ini"
  raiz_app=/protheus12/protheus_data/http-root/app-root
  mkdir -p "$raiz_app"
  [ -f "$raiz_app/index.html" ] || printf '<!doctype html><title>app-root</title>\n' > "$raiz_app/index.html"
fi

export DBAPI_URL=http://dbaccess-res:7891/dbapi.so
exec /protheus.sh
