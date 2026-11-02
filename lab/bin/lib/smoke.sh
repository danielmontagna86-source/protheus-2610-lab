#!/usr/bin/env bash
# lab smoke <release> - doctor -> compile LABHELLO -> TIR leitura -> limpeza -> PRONTO | FALHOU.
# Contrato: specs/001-protheus-2610-lab/contracts/smoke-report.md
set -uo pipefail
. "${PLAB_HOME:-/opt/plab}/lab/bin/lib/comum.sh"
LIB="${PLAB_HOME:-/opt/plab}/lab/bin/lib"

rel=${1:-}
validar_release "$rel" || exit 2

evid="${PLAB_HOME:-/opt/plab}/evidencias/$rel/$(carimbo)"
mkdir -p "$evid"
inicio=$(date -Iseconds)
passos_json=()
total=4

registrar() { # n nome status detalhe
  passos_json+=("$(jq -cn --argjson n "$1" --arg nome "$2" --arg status "$3" --arg detalhe "$4" \
    '{n:$n, nome:$nome, status:$status, detalhe:$detalhe}')")
}

finalizar() { # resultado codigo
  local passos
  passos=$(printf '%s\n' "${passos_json[@]}" | jq -s '.')
  jq -n --arg release "$rel" --arg inicio "$inicio" --arg fim "$(date -Iseconds)" \
        --arg resultado "$1" --argjson passos "$passos" \
        '{release:$release, inicio:$inicio, fim:$fim, passos:$passos, resultado:$resultado}' > "$evid/resumo.json"
  exit "$2"
}

falhou() { # n nome motivo
  registrar "$1" "$2" falhou "$3"
  printf '[%d/%d] %-18s FALHOU (%s)\n' "$1" "$total" "$2" "$3"
  echo "FALHOU $rel no passo $1/$2: $3 — evidencias: $evid"
  finalizar "FALHOU" $((10 + $1))
}

ok() { # n nome detalhe
  registrar "$1" "$2" ok "$3"
  printf '[%d/%d] %-18s OK   (%s)\n' "$1" "$total" "$2" "$3"
}

# 1. doctor
if "$LIB/doctor.sh" "$rel" > "$evid/doctor.log" 2>&1; then
  ok 1 doctor "WebApp, /app-root, REST e secret ok"
else
  falhou 1 doctor "$(grep -m1 FALHOU "$evid/doctor.log" | sed -E 's/^ +//')"
fi

# 2. Interface somente leitura (ANTES de compilar: na 2510 a compilacao derruba o /app-root ate o
#    AppServer reiniciar; o reinicio e feito pelo host em 'plab smoke'/'plab restart').
#    (login PO UI, modulo, abrir MATA010, conferir titulo) com Playwright.
#    O TIR 2.14.12 nao conclui o Setup nestes WebApps (ver cenarios/ui-smoke/README.md); com
#    PLAB_SMOKE_TIR=1 a suite TIR tambem roda, como passo informativo (nao bloqueia o PRONTO).
PLAB_EVID_DIR="$evid/ui" "$LIB/ui.sh" "$rel" > "$evid/ui.out" 2>&1
rc=$?
linha=$(grep -E '^\[ui\] (OK|FALHOU)' "$evid/ui.out" | tail -n 1 | sed 's/^\[ui\] //')
if [ "$rc" -eq 0 ]; then ok 2 interface "${linha:-ok}"
else falhou 2 interface "rc=$rc ${linha:-ver ui.out}"; fi
if [ "${PLAB_SMOKE_TIR:-0}" = 1 ]; then
  PLAB_EVID_DIR="$evid/tir" "$LIB/tir.sh" "$rel" "${PLAB_HOME:-/opt/plab}/cenarios/tir-smoke/SMOKETESTSUITE.py" > "$evid/tir.out" 2>&1
  echo "      (informativo) tir rc=$? — ver $evid/tir/tir.log"
fi

# 3. compile LABHELLO no ambiente de compilacao
PLAB_EVID_DIR="$evid" "$LIB/compile.sh" "$rel" "${PLAB_HOME:-/opt/plab}/cenarios/hello/LABHELLO.prw" > "$evid/compile.out" 2>&1
rc=$?
resumo=$(grep -m1 '^resumo compile' "$evid/compile.out" | sed 's/^resumo compile //')
if [ "$rc" -eq 0 ]; then ok 3 compile "$resumo"
else falhou 3 compile "rc=$rc ${resumo:-$(grep -m1 '^lab:' "$evid/compile.out")}"; fi

# 4. limpeza: nenhum arquivo temporario com credencial pode sobrar
sobras=$(find /tmp -maxdepth 1 \( -name 'plab-compile.*' -o -name 'plab-tir.*' \) -user "$(id -u)" 2>/dev/null | wc -l)
if [ "$sobras" -eq 0 ] && ! grep -rqs -F -f <(cat /run/secrets/plab_"$rel"_admin_password) "$evid"; then
  ok 4 limpeza "sem temporarios; nenhuma senha nas evidencias"
else
  falhou 4 limpeza "temporarios=$sobras ou senha encontrada nas evidencias"
fi

echo "PRONTO $rel — evidencias: $evid"
finalizar "PRONTO" 0
