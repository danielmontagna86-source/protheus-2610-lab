#!/usr/bin/env bash
# lab versions - versoes efetivamente instaladas na imagem.
set -uo pipefail

linha() { printf '%-14s %s\n' "$1" "$2"; }

linha "python"       "$(python --version 2>&1)"
linha "tir"          "$(python -c 'import importlib.metadata as m; print(m.version("tir_framework"))' 2>&1)"
linha "selenium"     "$(python -c 'import selenium; print(selenium.__version__)' 2>&1)"
linha "playwright"   "$(python -c 'import importlib.metadata as m; print(m.version("playwright"))' 2>&1)"
linha "chrome"       "$(google-chrome --version 2>&1)"
linha "chromedriver" "$(chromedriver --version 2>&1 | awk '{print $1, $2}')"
linha "node"         "$(node --version 2>&1)"
linha "advpls"       "$(advpls --version 2>&1 | head -n 1)"
linha "git"          "$(git --version 2>&1)"
