#!/usr/bin/env bash
# lab cenarios <release> [nome] - roda os cenarios de leitura de cenarios/ui-leitura/cenarios.json
# na release (todos, ou so o nome informado). Cada cenario usa a suite de interface somente leitura
# (cenarios/ui-smoke/smoke_ui.py) com modulo, menu, aba e titulo do JSON. Evidencias por cenario.
set -uo pipefail
. "${PLAB_HOME:-/opt/plab}/lab/bin/lib/comum.sh"
rel=${1:-}; so=${2:-}
validar_release "$rel" || exit 2
cfg="${PLAB_HOME:-/opt/plab}/cenarios/ui-leitura/cenarios.json"
base="${PLAB_HOME:-/opt/plab}/evidencias/$rel/cenarios-$(carimbo)"
mkdir -p "$base"
total=0; falhas=0; pulados=0; repeticoes=0

rodar_cenario() { # pasta_evidencias arquivo_saida (usa modulo, menu, aba, titulo e aviso do laco)
  PLAB_UI_MODULO=$modulo PLAB_UI_MENU=$menu PLAB_UI_ABA=$aba PLAB_UI_TITULO=$titulo PLAB_UI_AVISO=$aviso \
    PLAB_EVID_DIR="$1" "${PLAB_HOME:-/opt/plab}/lab/bin/lib/ui.sh" "$rel" > "$2" 2>&1
}

# Separador \x1f (nao e espaco em branco): com IFS de tab o read junta campos vazios (titulo/aviso).
while IFS=$'\x1f' read -r nome modulo menu aba titulo aviso releases; do
  [ -n "$so" ] && [ "$so" != "$nome" ] && continue
  total=$((total + 1))
  case ",$releases," in *",$rel,"*) ;; *) echo "[--] $nome: nao confirmado para a $rel (pulado)"; pulados=$((pulados + 1)); continue ;; esac
  rodar_cenario "$base/$nome" "$base/$nome.out"
  repetido=""
  # Unica repeticao aceita: a interface nova da 2610 falhou ao enviar a requisicao na tela de sessao
  # (aviso registrado por entrar_sessao em plab_pw.py) e a sessao nao abriu. Refaz o cenario desde o
  # login, uma vez, com evidencias separadas; qualquer outra falha conta direto (04/11/2026).
  if ! grep -q '^\[ui\] OK' "$base/$nome.out" && grep -q 'repetindo Entrar' "$base/$nome.out"; then
    mv "$base/$nome.out" "$base/$nome-1a-tentativa.out"
    rodar_cenario "$base/$nome-repeticao" "$base/$nome.out"
    repetido=" (refeito do login apos aviso de requisicao; 1a tentativa em $nome-1a-tentativa.out)"
    repeticoes=$((repeticoes + 1))
  fi
  linha=$(grep -E '^\[ui\] (OK|FALHOU)' "$base/$nome.out" | tail -n 1 | sed 's/^\[ui\] //')
  if grep -q '^\[ui\] OK' "$base/$nome.out"; then echo "[ok] $nome: $linha$repetido"
  else echo "[XX] $nome: ${linha:-ver $base/$nome.out}$repetido"; falhas=$((falhas + 1)); fi
done < <(jq -r '.cenarios[] | [.nome, .modulo, (.menu|join(">")), .aba, (.titulo // ""), (.aviso // ""), (.releases|join(","))] | join("\u001f")' "$cfg")
echo "cenarios $rel: total=$total falhas=$falhas pulados=$pulados repeticoes=$repeticoes evidencias=$base"
[ "$falhas" -eq 0 ]
