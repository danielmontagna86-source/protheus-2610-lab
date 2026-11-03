#!/usr/bin/env bash
# lab setup - assistente de IA do Protheus 2610 Lab (contrato: specs/001-protheus-2610-lab/contracts/lab-setup-cli.md)
#   lab setup [--release 2610|2510] [--ia claude,codex,opencode,gemini] [--auth conta|api_key]
#             [--with-exemplos] [--nao-interativo] [--sem-smoke]
# Passos: doctor -> escolha das IAs -> instala CLI fixada -> autentica -> teste "OK" ->
#         publica skills -> gera AGENTS/CLAUDE/GEMINI.md -> smoke -> resumo.
# Idempotente: estado em ~/.config/lab/state.json (sem segredo).
set -uo pipefail
PLAB_HOME=${PLAB_HOME:-/opt/plab}
SETUP="$PLAB_HOME/lab/setup"
# shellcheck source=lib/estado.sh
. "$SETUP/lib/estado.sh"
# shellcheck source=lib/segredos.sh
. "$SETUP/lib/segredos.sh"
# shellcheck source=lib/skills.sh
. "$SETUP/lib/skills.sh"
# shellcheck source=lib/templates.sh
. "$SETUP/lib/templates.sh"
# shellcheck source=providers/claude.sh
. "$SETUP/providers/claude.sh"
# shellcheck source=providers/codex.sh
. "$SETUP/providers/codex.sh"
# shellcheck source=providers/opencode.sh
. "$SETUP/providers/opencode.sh"
# shellcheck source=providers/gemini.sh
. "$SETUP/providers/gemini.sh"

NPM_PREFIXO="${HOME}/.npm-global"
# PLAB_WORKSPACE existe so para os testes locais (lab/tests); no lab e sempre /workspace.
WORKSPACE=${PLAB_WORKSPACE:-/workspace}
IAS_SUPORTADAS="claude codex opencode gemini"

rel=""; ias=""; auth=""; exemplos=""; interativo=1; smoke=1
while [ $# -gt 0 ]; do
  case "$1" in
    --release) rel=$2; shift 2 ;;
    --ia) ias=${2//,/ }; shift 2 ;;
    --auth) auth=$2; shift 2 ;;
    --with-exemplos) exemplos=--with-exemplos; shift ;;
    --nao-interativo) interativo=0; shift ;;
    --sem-smoke) smoke=0; shift ;;
    *) echo "opcao desconhecida: $1" >&2; exit 2 ;;
  esac
done
[ -t 0 ] || interativo=0

estado_iniciar
estado_sanear
segredos_preparar
mkdir -p "$NPM_PREFIXO"

echo "== 1/7 release"
if [ -z "$rel" ]; then
  respondendo=()
  for r in 2610 2510; do "$PLAB_HOME/lab/bin/lib/doctor.sh" "$r" >/dev/null 2>&1 && respondendo+=("$r"); done
  rel=${respondendo[0]:-}
  if [ "${#respondendo[@]}" -gt 1 ] && [ "$interativo" = 1 ]; then
    read -r -p "Releases respondendo: ${respondendo[*]}. Qual usar? [$rel]: " escolha
    case "${escolha:-$rel}" in 2610|2510) rel=${escolha:-$rel} ;; *) echo "release invalida: $escolha" >&2; exit 2 ;; esac
  fi
fi
[ -n "$rel" ] || { echo "nenhuma release respondendo. No host: plab up 2610"; exit 3; }
"$PLAB_HOME/lab/bin/lib/doctor.sh" "$rel" || exit 3
estado_set '.release' "$rel"

echo "== 2/7 IAs"
if [ -z "$ias" ]; then
  if [ "$interativo" = 1 ]; then
    read -r -p "IAs (separadas por espaco) [$IAS_SUPORTADAS]: " ias
  fi
  ias=${ias:-$IAS_SUPORTADAS}
fi
for ia in $ias; do
  case " $IAS_SUPORTADAS " in *" $ia "*) ;; *) echo "IA nao suportada: $ia (suportadas: $IAS_SUPORTADAS)"; exit 2 ;; esac
done

resumo=()
dirs_skills=()
for ia in $ias; do
  echo "== 3-5/7 $ia"
  # Modos que a IA suporta (provider pode declarar <ia>_modos; padrao: conta e api_key).
  modos="conta api_key"
  if declare -F "${ia}_modos" >/dev/null; then modos=$("${ia}_modos"); fi
  modo=${auth:-$(estado_get ".ias.$ia.auth")}
  if [ -z "$modo" ]; then
    if [ "$interativo" = 1 ]; then read -r -p "  autenticacao de $ia [${modos// //}] (${modos%% *}): " modo; fi
    modo=${modo:-${modos%% *}}
  fi
  case "$modo" in conta|api_key) ;; *) echo "  modo invalido: $modo"; exit 2 ;; esac
  case " $modos " in
    *" $modo "*) ;;
    *) echo "  $ia: modo $modo nao suportado (suportado: $modos)"
       st="nao_suportado(modo $modo; use: $modos)"
       estado_set ".ias.$ia.estado" "$st"; resumo+=("$ia|$modo|$st"); continue ;;
  esac
  estado_set ".ias.$ia.auth" "$modo"

  if ! "${ia}_instalar"; then estado_set ".ias.$ia.estado" "falhou(instalacao)"; resumo+=("$ia|$modo|falhou(instalacao)"); continue; fi
  case "$ia" in
    claude) versao=${PLAB_CLAUDE_CODE:-} ;;
    codex) versao=${PLAB_CODEX:-} ;;
    opencode) versao=${PLAB_OPENCODE:-} ;;
    gemini) versao=${PLAB_GEMINI_CLI:-} ;;
  esac
  estado_set ".ias.$ia.versao" "$versao"

  # Sem captura de saida: o login (URL, codigo, perguntas) precisa ir direto ao terminal.
  "${ia}_autenticar" "$modo" "$interativo"; rc=$?
  if [ $rc -eq 2 ]; then
    st="nao_testado(sem credencial: modo $modo exige interacao do dono)"
  elif [ $rc -ne 0 ]; then
    st="falhou(autenticacao)"
  elif teste=$("${ia}_testar"); then
    st="testado_ok"
  else
    # So a categoria vai para o state.json (contrato: sem segredo). A saida da CLI pode ecoar parte
    # mascarada da chave, entao aparece so no terminal, para o diagnostico.
    st="falhou(teste)"
    echo "  $ia: teste falhou: ${teste}" >&2
  fi
  estado_set ".ias.$ia.estado" "$st"
  resumo+=("$ia|$modo|$st")
  dirs_skills+=("$("${ia}_dir_skills")")
done

echo "== 6/7 skills e instrucoes do workspace"
nomes=""
for d in "${dirs_skills[@]}"; do
  nomes=$(publicar_skills "$d" "$exemplos" | sort -u)
  estado_set ".skills.\"$d\"" "$(echo "$nomes" | tr '\n' ' ' | sed 's/ $//')"
  echo "  $(echo "$nomes" | wc -l) skills em $d"
done
# shellcheck disable=SC2016  # os acentos graves sao markdown, nao expansao
lista=$(echo "$nomes" | sed '/^$/d; s/^/- `/; s/$/`/')
gerar_instrucoes "$rel" "${lista:-- (nenhuma IA configurada)}" "$WORKSPACE"
estado_set '.workspace.instrucoes' "AGENTS.md CLAUDE.md GEMINI.md"
echo "  AGENTS.md, CLAUDE.md e GEMINI.md atualizados em $WORKSPACE (bloco plab)"

echo "== 7/7 smoke"
st_smoke="pulado"
if [ "$smoke" = 1 ]; then
  if "$PLAB_HOME/lab/bin/lib/smoke.sh" "$rel"; then st_smoke=PRONTO; else st_smoke="FALHOU (ver evidencias)"; fi
fi

echo
echo "Resumo do lab setup (release $rel)"
printf '  %-9s %-8s %s\n' IA modo estado
for l in "${resumo[@]}"; do IFS='|' read -r a m s <<<"$l"; printf '  %-9s %-8s %s\n' "$a" "$m" "$s"; done
echo "  smoke: $st_smoke"
# Codigo 1 quando o smoke falhou ou alguma IA ficou em falhou(...). nao_testado e nao_suportado
# nao reprovam: sao o resultado esperado de --nao-interativo e de modo nao documentado pela CLI.
ias_falhas=""
for l in "${resumo[@]}"; do
  IFS='|' read -r a _ s <<<"$l"
  case "$s" in falhou\(*) ias_falhas+=" $a" ;; esac
done
case "$st_smoke" in PRONTO|pulado) ;; *) exit 1 ;; esac
if [ -n "$ias_falhas" ]; then echo "  IAs com falha:$ias_falhas"; exit 1; fi
exit 0
