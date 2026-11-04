#!/usr/bin/env bash
# shellcheck disable=SC2016  # stubs gravados com $ literais, de proposito
# Testa estados e codigo de saida do "lab setup" (L6 da revisao) sem container e sem rede:
# providers, doctor, smoke e publicacao de skills sao stubs; HOME e workspace temporarios.
#   test_setup_estados.sh
set -uo pipefail
raiz=$(cd "$(dirname "$0")/../.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
falhas=0
confere() { # descricao obtido esperado
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FALHA $1: obtido [$2], esperado [$3]"; falhas=$((falhas + 1)); fi
}

home="$tmp/plab"
mkdir -p "$home/lab/setup/lib" "$home/lab/setup/providers" "$home/lab/bin/lib" "$home/templates"
cp "$raiz/lab/setup/lab-setup.sh" "$home/lab/setup/"
cp "$raiz/lab/setup/lib/estado.sh" "$raiz/lab/setup/lib/segredos.sh" "$raiz/lab/setup/lib/templates.sh" "$home/lab/setup/lib/"
cp "$raiz/templates/agent-rules.md.tmpl" "$home/templates/"
printf 'publicar_skills() { echo skill-falsa; }\n' > "$home/lab/setup/lib/skills.sh"
printf '#!/bin/bash\nexit 0\n' > "$home/lab/bin/lib/doctor.sh"
printf '#!/bin/bash\nexit "${FALSO_SMOKE:-0}"\n' > "$home/lab/bin/lib/smoke.sh"
chmod +x "$home/lab/bin/lib/"*.sh
# Provider falso: FALSO_<IA>_AUT e FALSO_<IA>_TESTE dao o codigo de autenticar e testar.
for ia in claude codex opencode gemini; do
  IA=${ia^^}
  cat > "$home/lab/setup/providers/$ia.sh" <<P
${ia}_instalar() { :; }
${ia}_autenticar() { return "\${FALSO_${IA}_AUT:-0}"; }
${ia}_testar() { [ "\${FALSO_${IA}_TESTE:-0}" = 0 ] && return 0; echo "erro da CLI: chave sk-falsa-1234 recusada"; return 1; }
${ia}_dir_skills() { echo "\$HOME/.$ia/skills"; }
P
done
echo 'gemini_modos() { echo api_key; }' >> "$home/lab/setup/providers/gemini.sh"

roda() { # variaveis FALSO_*=... ; argumentos depois de --
  local vars=()
  while [ "$1" != -- ]; do vars+=("$1"); shift; done; shift
  env HOME="$tmp/home" PLAB_HOME="$home" PLAB_WORKSPACE="$tmp/ws" "${vars[@]}" \
    bash "$home/lab/setup/lab-setup.sh" --release 2610 --nao-interativo "$@" > "$tmp/saida" 2>&1 < /dev/null
  echo $?
}
mkdir -p "$tmp/ws"
estado() { jq -r ".ias.$1.estado" "$tmp/home/.config/lab/state.json"; }

confere "tudo ok: codigo 0" "$(roda -- --ia claude,codex --auth conta)" 0
confere "tudo ok: estado" "$(estado claude)" testado_ok
confere "sem credencial (nao interativo): codigo 0" "$(roda FALSO_CLAUDE_AUT=2 -- --ia claude --auth conta)" 0
confere "sem credencial: nao_testado" "$(estado claude | cut -c1-12)" "nao_testado("
confere "teste da IA falhou: codigo 1" "$(roda FALSO_CODEX_TESTE=1 -- --ia claude,codex --auth conta)" 1
confere "teste da IA falhou: so a categoria no estado" "$(estado codex)" "falhou(teste)"
confere "saida da CLI fora do state.json" "$(grep -c 'sk-falsa' "$tmp/home/.config/lab/state.json")" 0
confere "saida da CLI no terminal" "$(grep -c 'sk-falsa' "$tmp/saida")" 1
grep -q 'IAs com falha: codex' "$tmp/saida"; confere "resumo cita a IA com falha" "$?" 0
confere "autenticacao falhou: codigo 1" "$(roda FALSO_CLAUDE_AUT=1 -- --ia claude --auth conta)" 1
confere "smoke falhou: codigo 1" "$(roda FALSO_SMOKE=14 -- --ia claude --auth conta)" 1
confere "modo nao suportado nao reprova" "$(roda -- --ia gemini --auth conta)" 0
confere "modo nao suportado: estado" "$(estado gemini | cut -c1-14)" "nao_suportado("

# Estado de versao anterior com saida da CLI: fica so a categoria.
jq '.ias.codex.estado = "falhou(teste: erro sk-antigo-9999)"' "$tmp/home/.config/lab/state.json" > "$tmp/e" \
  && mv "$tmp/e" "$tmp/home/.config/lab/state.json"
roda -- --ia claude --auth conta --sem-smoke >/dev/null
confere "estado antigo saneado" "$(estado codex)" "falhou(teste)"
confere "nada do estado antigo sobrou" "$(grep -c 'sk-antigo' "$tmp/home/.config/lab/state.json")" 0

echo "falhas: $falhas"
[ "$falhas" -eq 0 ]
