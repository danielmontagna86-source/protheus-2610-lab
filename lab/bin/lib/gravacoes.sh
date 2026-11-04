#!/usr/bin/env bash
# lab gravacoes <release> [nome] - cenarios de GRAVACAO de cenarios/ui-gravacao/gravacoes.json:
# cada um inclui um registro de teste pela rotina padrao, confere no browse, exclui pela propria
# rotina e confere que sumiu. Grava no banco do lab: exige PLAB_GRAVACAO_AUTORIZADA=sim
# (autorizacao do dono) e uma copia da base feita antes no host (plab snapshot <rel>).
set -uo pipefail
. "${PLAB_HOME:-/opt/plab}/lab/bin/lib/comum.sh"
rel=${1:-}; so=${2:-}
validar_release "$rel" || exit 2
if [ "${PLAB_GRAVACAO_AUTORIZADA:-}" != "sim" ]; then
  erro "cenarios de gravacao alteram o banco do lab. Antes: 'plab snapshot $rel' no host e autorizacao"
  erro "do dono; depois rode com PLAB_GRAVACAO_AUTORIZADA=sim (e 'plab restore $rel <copia>' ao final)"
  exit 3
fi
cfg="${PLAB_HOME:-/opt/plab}/cenarios/ui-gravacao/gravacoes.json"
base="${PLAB_HOME:-/opt/plab}/evidencias/$rel/gravacoes-$(carimbo)"
mkdir -p "$base"
total=0; falhas=0; pulados=0

rodar_gravacao() { # pasta_evidencias arquivo_saida (usa nome do laco)
  PLAB_GRAV_NOME=$nome PLAB_EVID_DIR="$1" PYTHONPATH="${PLAB_HOME:-/opt/plab}/lab/tir${PYTHONPATH:+:$PYTHONPATH}" \
    timeout "${PLAB_UI_LIMITE:-900}" python -u "${PLAB_HOME:-/opt/plab}/cenarios/ui-gravacao/gravacao_ui.py" "$rel" \
    > "$2" 2>&1
}

while IFS=$'\x1f' read -r nome releases; do
  [ -n "$so" ] && [ "$so" != "$nome" ] && continue
  total=$((total + 1))
  case ",$releases," in *",$rel,"*) ;; *) echo "[--] $nome: nao confirmado para a $rel (pulado)"; pulados=$((pulados + 1)); continue ;; esac
  rodar_gravacao "$base/$nome" "$base/$nome.out"
  repetido=""
  # Mesma regra do 'lab cenarios' (issue #21): refaz desde o login, uma vez, so quando a sessao nao
  # abriu por causa do aviso de requisicao e nenhum formulario foi preenchido (nada gravado).
  if ! grep -q '^\[grav\] OK' "$base/$nome.out" && grep -q 'aviso de requisicao' "$base/$nome.out" \
     && ! grep -q '^\[grav\] preenchidos' "$base/$nome.out"; then
    mv "$base/$nome.out" "$base/$nome-1a-tentativa.out"
    rodar_gravacao "$base/$nome-repeticao" "$base/$nome.out"
    repetido=" (refeito do login apos aviso de requisicao)"
  fi
  linha=$(grep -E '^\[grav\] (OK|FALHOU)' "$base/$nome.out" | tail -n 1 | sed 's/^\[grav\] //')
  if grep -q '^\[grav\] OK' "$base/$nome.out"; then echo "[ok] $nome: $linha$repetido"
  else echo "[XX] $nome: ${linha:-ver $base/$nome.out}$repetido"; falhas=$((falhas + 1)); fi
done < <(jq -r '.cenarios[] | [.nome, (.releases|join(","))] | join("\u001f")' "$cfg")
echo "gravacoes $rel: total=$total falhas=$falhas pulados=$pulados evidencias=$base"
[ "$falhas" -eq 0 ]
