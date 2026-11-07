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
# Fonte reserva: base vazia (so a empresa TESTE com o dicionario). Browse sem registros conta como
# aberto (PLAB_UI_BASE_VAZIA) e cenarios que abrem um registro (Visualizar) sao pulados.
base_vazia=""
if fonte_reserva "$rel"; then
  base_vazia=sim
  echo "fonte reserva na $rel: base vazia; browse sem registros conta como aberto e Visualizar e pulado"
fi

rodar_cenario() { # pasta_evidencias arquivo_saida (usa modulo, menu, aba, titulo, aviso, parametros e help do laco)
  PLAB_UI_BASE_VAZIA=$base_vazia PLAB_UI_MODULO=$modulo PLAB_UI_MENU=$menu PLAB_UI_ABA=$aba PLAB_UI_TITULO=$titulo PLAB_UI_AVISO=$aviso \
    PLAB_UI_PARAMETROS=$parametros PLAB_UI_HELP=$ajuda PLAB_UI_VISUALIZAR=$visualizar \
    PLAB_EVID_DIR="$1" "${PLAB_HOME:-/opt/plab}/lab/bin/lib/ui.sh" "$rel" > "$2" 2>&1
}

# Separador \x1f (nao e espaco em branco): com IFS de tab o read junta campos vazios (titulo/aviso).
while IFS=$'\x1f' read -r nome modulo menu aba titulo aviso parametros ajuda visualizar releases r_menu r_aba r_titulo; do
  [ -n "$so" ] && [ "$so" != "$nome" ] && continue
  total=$((total + 1))
  case ",$releases," in *",$rel,"*) ;; *) echo "[--] $nome: nao confirmado para a $rel (pulado)"; pulados=$((pulados + 1)); continue ;; esac
  if [ -n "$base_vazia" ] && [ "$visualizar" = 1 ]; then
    echo "[--] $nome: abre um registro e a base da reserva e vazia (pulado)"; pulados=$((pulados + 1)); continue
  fi
  # Bloco "reserva" do JSON: menu, aba e titulo da base da reserva quando diferem (menu da imagem).
  # Titulo "-" = sem ajuste; titulo vazio = conferir a grade em vez do titulo.
  if [ -n "$base_vazia" ]; then
    [ -n "$r_menu" ] && menu=$r_menu
    [ -n "$r_aba" ] && aba=$r_aba
    [ "$r_titulo" != "-" ] && titulo=$r_titulo
  fi
  rodar_cenario "$base/$nome" "$base/$nome.out"
  repetido=""; n=0
  # Unica repeticao aceita: a interface nova da 2610 falhou ao enviar a requisicao na tela de sessao
  # (aviso registrado por entrar_sessao em plab_pw.py; issue #21) e a sessao nao abriu. Refaz o
  # cenario desde o login, ate PLAB_REPETICOES_AVISO vezes (padrao 3), com evidencias separadas;
  # qualquer outra falha conta direto.
  while ! grep -q '^\[ui\] OK' "$base/$nome.out" && grep -q 'aviso de requisicao' "$base/$nome.out" \
        && [ "$n" -lt "${PLAB_REPETICOES_AVISO:-3}" ]; do
    n=$((n + 1))
    mv "$base/$nome.out" "$base/$nome-tentativa$n.out"
    rodar_cenario "$base/$nome-repeticao$n" "$base/$nome.out"
    repetido=" (refeito do login $n vez(es) apos aviso de requisicao; tentativas anteriores em $nome-tentativa<n>.out)"
    repeticoes=$((repeticoes + 1))
  done
  linha=$(grep -E '^\[ui\] (OK|FALHOU)' "$base/$nome.out" | tail -n 1 | sed 's/^\[ui\] //')
  if grep -q '^\[ui\] OK' "$base/$nome.out"; then echo "[ok] $nome: $linha$repetido"
  else echo "[XX] $nome: ${linha:-ver $base/$nome.out}$repetido"; falhas=$((falhas + 1)); fi
done < <(jq -r '.cenarios[] | [.nome, .modulo, (.menu|join(">")), .aba, (.titulo // ""), (.aviso // ""), (.parametros // ""), (.help // ""), (if .visualizar == true then "1" else "" end), (.releases|join(",")), ((.reserva.menu // [])|join(">")), (.reserva.aba // ""), (if (.reserva // {})|has("titulo") then .reserva.titulo else "-" end)] | join("\u001f")' "$cfg")
echo "cenarios $rel: total=$total falhas=$falhas pulados=$pulados repeticoes=$repeticoes evidencias=$base"
[ "$falhas" -eq 0 ]
