#!/usr/bin/env bash
# Confere que fontes AdvPL/TLPP do repositorio estao em CP1252 + CRLF (Principio V).
# Falha se houver LF sem CR antes, ou sequencia que so faz sentido como UTF-8 multibyte.
set -euo pipefail
raiz=${1:-$(cd "$(dirname "$0")/../.." && pwd)}
falhas=0
total=0
while IFS= read -r -d '' arq; do
  total=$((total + 1))
  lf=$(tr -cd '\n' < "$arq" | wc -c)
  crlf=$(LC_ALL=C grep -c $'\r$' "$arq" || true)
  if [ "$lf" -ne "$crlf" ]; then
    echo "FALHA LF sem CR ($crlf de $lf linhas com CRLF): $arq"; falhas=$((falhas + 1)); continue
  fi
  # UTF-8 multibyte valido (2 bytes C2-DF + 80-BF) indica gravacao em UTF-8.
  if LC_ALL=C grep -qP '[\xC2-\xDF][\x80-\xBF]' "$arq"; then
    echo "FALHA parece UTF-8: $arq"; falhas=$((falhas + 1)); continue
  fi
  if [ "$(head -c 3 "$arq" | od -An -tx1 | tr -d ' ')" = "efbbbf" ]; then
    echo "FALHA BOM UTF-8: $arq"; falhas=$((falhas + 1)); continue
  fi
  echo "ok   $arq"
done < <(find "$raiz" -path "$raiz/.git" -prune -o -type f \( -iname '*.prw' -o -iname '*.prx' -o -iname '*.tlpp' -o -iname '*.ch' \) -print0)
echo "fontes: $total  falhas: $falhas"
[ "$total" -gt 0 ] && [ "$falhas" -eq 0 ]
