#!/usr/bin/env bash
# lab ui <release> - smoke de interface (Playwright) somente leitura. Ver cenarios/ui-smoke/README.md.
set -uo pipefail
. "${PLAB_HOME:-/opt/plab}/lab/bin/lib/comum.sh"
rel=${1:-}
validar_release "$rel" || exit 2
export PLAB_EVID_DIR=${PLAB_EVID_DIR:-/tmp/plab-ui-$rel-$(carimbo)}
PYTHONPATH="${PLAB_HOME:-/opt/plab}/lab/tir${PYTHONPATH:+:$PYTHONPATH}" \
  timeout "${PLAB_UI_LIMITE:-600}" python -u "${PLAB_HOME:-/opt/plab}/cenarios/ui-smoke/smoke_ui.py" "$rel"
rc=$?
[ "$rc" -eq 124 ] && erro "smoke de interface excedeu o limite de tempo"
echo "resumo ui $rel: rc=$rc evidencias=$PLAB_EVID_DIR"
exit "$rc"
