#!/usr/bin/env bash
# Publicacao das skills nos diretorios de cada CLI.
#  - do lab: /opt/plab/skills/* (testes-protheus, compilar-advpls-lab);
#  - EngPro (totvs/engpro-advpl-tlpp-skills, MIT): clonada no commit PLAB_ENGPRO_COMMIT, nao vendorizada;
#  - exemplos validados (dan-atilio/AdvPL, GPL-3.0): so com --with-exemplos, no commit PLAB_EXEMPLOS_COMMIT.
ENGPRO_URL="https://github.com/totvs/engpro-advpl-tlpp-skills.git"
EXEMPLOS_URL="https://github.com/dan-atilio/AdvPL.git"
CACHE_PLAB="${HOME}/.cache/plab"

# clonar_no_commit <url> <commit> <destino>
clonar_no_commit() {
  local url=$1 commit=$2 dst=$3
  if [ -d "$dst/.git" ] && [ "$(git -C "$dst" rev-parse HEAD 2>/dev/null)" = "$commit" ]; then return 0; fi
  rm -rf "$dst"; mkdir -p "$dst"
  git -C "$dst" init -q && git -C "$dst" remote add origin "$url" \
    && git -C "$dst" fetch -q --depth 1 origin "$commit" && git -C "$dst" checkout -q FETCH_HEAD
}

# substituir_skill <origem> <dir_destino> - troca a skill inteira. A copia da imagem vem somente
# leitura (root, 0444/0555); sem dar escrita ao usuario antes, o rm da versao antiga falha.
substituir_skill() {
  local alvo; alvo="$2/$(basename "$1")"
  [ -e "$alvo" ] && chmod -R u+w "$alvo" 2>/dev/null
  rm -rf "${alvo:?}"
  cp -R "$1" "$2/" && chmod -R u+rwX,go+rX "$alvo"
}

# publicar_skills <dir_destino> [--with-exemplos] - imprime os nomes publicados
publicar_skills() {
  local dst=$1 exemplos=${2:-}
  mkdir -p "$dst"
  local s
  for s in "${PLAB_HOME:-/opt/plab}"/skills/*/; do
    [ -f "$s/SKILL.md" ] || continue
    substituir_skill "$s" "$dst"
    basename "$s"
  done
  if [ -n "${PLAB_ENGPRO_COMMIT:-}" ]; then
    clonar_no_commit "$ENGPRO_URL" "$PLAB_ENGPRO_COMMIT" "$CACHE_PLAB/engpro" || { echo "aviso: falha ao clonar EngPro" >&2; return 0; }
    for s in "$CACHE_PLAB"/engpro/skills/*/*/; do
      [ -f "$s/SKILL.md" ] || continue
      substituir_skill "$s" "$dst"
      basename "$s"
    done
  fi
  if [ "$exemplos" = "--with-exemplos" ] && [ -n "${PLAB_EXEMPLOS_COMMIT:-}" ]; then
    clonar_no_commit "$EXEMPLOS_URL" "$PLAB_EXEMPLOS_COMMIT" "$CACHE_PLAB/exemplos" \
      && echo "advpl-exemplos (referencia em $CACHE_PLAB/exemplos)"
  fi
}
