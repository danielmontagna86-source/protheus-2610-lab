#!/usr/bin/env bash
# lab compile <release> <fonte...> - compila fontes AdvPL/TLPP no ambiente de compilacao da release.
# Regras (skill compilar-advpls-lab):
#  - script do advpls em diretorio temporario 0700, arquivo 0600, apagado por trap;
#  - senha so do secret montado, nunca em argumento/log;
#  - nomes de arquivo em minusculas (exigencia do AppServer Linux);
#  - resultado por SUCCESS/WARN/ERROR/FATAL: um FATAL ou ERROR invalida o lote.
# Variaveis opcionais: PLAB_EVID_DIR (onde gravar compile.log), PLAB_INCLUDES (dir de includes
# no container lab; padrao /opt/plab-includes).
set -uo pipefail
. "${PLAB_HOME:-/opt/plab}/lab/bin/lib/comum.sh"

rel=${1:-}; shift || true
validar_release "$rel" || exit 2
[ $# -gt 0 ] || { erro "informe ao menos um fonte"; exit 2; }

host=$(host_release "$rel")
amb=$(valor_release "$rel" ENV_COMPILA)
[ -n "$amb" ] || { erro "PLAB_${rel}_ENV_COMPILA vazio"; exit 2; }
senha=$(senha_admin "$rel") || exit 3
usuario=${PLAB_ADMIN_USER:-Admin}
# Defeito do advpls (TDS-LS 2.2.7), verificado em 2026-11-02: "$" no psw do script trava o
# parser (loop em std::string::find, sem nenhuma saida). Falha cedo em vez de pendurar.
case "$senha" in
  *'$'*) unset senha
         erro "a senha do $usuario da $rel contem '\$', que trava o advpls cli. Troque a senha desse usuario no Protheus por uma sem '\$' e atualize PLAB_${rel}_ADMIN_PASSWORD no .env (ver README > Compilacao)."
         exit 22 ;;
esac

tmp=$(mktemp -d /tmp/plab-compile.XXXXXX)
chmod 0700 "$tmp"
mkdir -p "$tmp/include"
trap 'rm -rf "$tmp"' EXIT

# Copia os fontes com nome minusculo, preservando bytes (CP1252/CRLF).
lista=()
for f in "$@"; do
  [ -f "$f" ] || { erro "fonte nao encontrado: $f"; exit 2; }
  destino="$tmp/src/$(basename "$f" | tr '[:upper:]' '[:lower:]')"
  mkdir -p "$tmp/src"
  cp -- "$f" "$destino"
  lista+=("$destino")
done
programas=$(IFS=,; echo "${lista[*]}")

script="$tmp/compile.ini"
umask 077
{
  printf 'showConsoleOutput=true\n\n'
  printf '[authentication]\naction=authentication\nserver=%s\nport=%s\nsecure=0\nbuild=AUTO\n' "$host" "$PLAB_PORT_TCP_INTERNA"
  printf 'environment=%s\nuser=%s\npsw=%s\n\n' "$amb" "$usuario" "$senha"
  printf '[compile]\naction=compile\nprogram=%s\nrecompile=T\n' "$programas"
  # "includes" e obrigatorio; o pre-compilador do advpls roda AQUI no lab e exige PRTOPDEF.CH
  # em todo .prw. O advpls precisa de ESCRITA no diretorio de includes (verificado em
  # 2026-11-02: o volume montado ro falha com C2090), entao usa-se uma copia temporaria.
  printf 'includes=%s\n' "$tmp/include"
} | iconv -f UTF-8 -t CP1252 > "$script"
inc_origem=${PLAB_INCLUDES:-/opt/plab-includes}
[ -f "$inc_origem/PRTOPDEF.CH" ] || [ -f "$inc_origem/prtopdef.ch" ] || {
  erro "includes ausentes em $inc_origem (rode no host: plab up lab, que semeia o volume includes)"; exit 4; }
cp -a "$inc_origem/." "$tmp/include/"
unset senha

log="$tmp/compile.log"
# O advpls tenta primeiro conexao segura; o multiprotocolo recusa e fecha o socket, e o advpls
# morre por SIGPIPE (rc 141, sem log). Ignorar SIGPIPE (herdado no exec) deixa ele cair para
# a conexao convencional, como ele mesmo faz quando sobrevive.
limite=${PLAB_COMPILE_TIMEOUT:-300}
( trap '' PIPE; exec timeout "$limite" advpls cli "$script" ) > "$log" 2>&1
rc=$?
[ "$rc" -eq 124 ] && echo "[ERROR] advpls excedeu ${limite}s (PLAB_COMPILE_TIMEOUT) e foi interrompido" >> "$log"

# Saneia: nada que pareca a linha psw sai do diretorio temporario.
sed -i -E 's/(psw[[:space:]]*=).*/\1***/I' "$log"

n_ok=$(grep -c '\[SUCCESS\]' "$log" || true)
n_warn=$(grep -Eci '\[(WARN|WARNING)\]' "$log" || true)
n_err=$(grep -Ec '\[ERROR\]' "$log" || true)
n_fatal=$(grep -Ec '\[FATAL\]' "$log" || true)
total=${#lista[@]}

if [ -n "${PLAB_EVID_DIR:-}" ]; then
  mkdir -p "$PLAB_EVID_DIR" && cp "$log" "$PLAB_EVID_DIR/compile.log"
fi

cat "$log"
echo "resumo compile $rel/$amb: fontes=$total SUCCESS=$n_ok WARN=$n_warn ERROR=$n_err FATAL=$n_fatal advpls_rc=$rc"

if grep -Eqi 'COMPILEERROR-300|RPO.*(em uso|in use)' "$log"; then
  erro "RPO em uso (COMPILEERROR-300): feche as sessoes do ambiente $amb (inclusive TIR) e repita"
  exit 21
fi
if [ "$n_fatal" -gt 0 ] || [ "$n_err" -gt 0 ] || [ "$n_ok" -ne "$total" ] || [ "$rc" -ne 0 ]; then
  erro "compilacao invalida (um FATAL/ERROR invalida o lote)"
  exit 20
fi
echo "compile $rel: OK"
case " ${PLAB_REINICIAR_APOS_COMPILAR:-2510} " in
  *" $rel "*) echo "aviso: na $rel a compilacao derruba a interface nova (/app-root) ate o AppServer reiniciar." \
                   "Rode no host: plab restart $rel" ;;
esac
