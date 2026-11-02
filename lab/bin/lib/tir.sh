#!/usr/bin/env bash
# lab tir <release> <suite.py> - executa uma suite TIR contra a release, com config temporaria.
# Regras (skill testes-protheus + EngPro tir-test-generator 5.1.0):
#  - config.json gerado em diretorio 0700, arquivo 0600, apagado por trap; senha lida do secret;
#  - Protheus com login PO UI: POUILogin=true, POUI=false; home classica: NewHome=false;
#  - Chrome headless com o chromedriver fixado na imagem (sem download em runtime).
# A suite le o caminho da config em PLAB_TIR_CONFIG. Evidencias em PLAB_EVID_DIR (opcional).
set -uo pipefail
. "${PLAB_HOME:-/opt/plab}/lab/bin/lib/comum.sh"

rel=${1:-}; suite=${2:-}
validar_release "$rel" || exit 2
[ -f "$suite" ] || { erro "suite nao encontrada: $suite"; exit 2; }

tmp=$(mktemp -d /tmp/plab-tir.XXXXXX)
chmod 0700 "$tmp"
trap 'rm -rf "$tmp"' EXIT
# Evidencias fora do $tmp (que o trap apaga) por padrao.
evid=${PLAB_EVID_DIR:-${PLAB_HOME:-/opt/plab}/evidencias/$rel/tir-$(carimbo)}
mkdir -p "$evid" "$tmp/log" "$tmp/shots"

export PLAB_TIR_CONFIG="$tmp/config.json"
umask 077
# JSON montado em Python para escapar a senha corretamente; a senha vem do secret, nao do ambiente.
python - "$rel" "$PLAB_TIR_CONFIG" "$tmp" <<'PY'
import json, os, sys
rel, destino, tmp = sys.argv[1], sys.argv[2], sys.argv[3]
with open(f"/run/secrets/plab_{rel}_admin_password", encoding="utf-8") as f:
    senha = f.read().strip("\r\n")
if not senha:
    sys.exit("senha do Admin vazia no secret")
cfg = {
    "Url": f"http://{os.environ[f'PLAB_{rel}_HOST']}:1234/webapp/",
    "Browser": "Chrome",
    "Environment": os.environ[f"PLAB_{rel}_ENV"],
    "User": os.environ.get("PLAB_ADMIN_USER", "Admin"),
    "Password": senha,
    "Language": "pt-br",
    "POUI": False,
    "POUILogin": True,
    "NewHome": False,
    "Headless": True,
    "ChromeDriverAutoInstall": False,
    "TimeOut": int(os.environ.get("PLAB_TIR_TIMEOUT", "180")),
    "LogFolder": os.path.join(tmp, "log"),
    "ScreenshotFolder": os.path.join(tmp, "shots"),
}
with open(destino, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
PY
[ -s "$PLAB_TIR_CONFIG" ] || { erro "falha ao gerar config TIR"; exit 3; }

echo "tir $rel: $(basename "$suite") em $(url_webapp "$rel") (ambiente $(valor_release "$rel" ENV))"
( cd "$tmp" && PLAB_RELEASE="$rel" PYTHONPATH="${PLAB_HOME:-/opt/plab}/lab/tir${PYTHONPATH:+:$PYTHONPATH}" \
    timeout "${PLAB_TIR_LIMITE:-900}" python -u "$suite" ) > "$tmp/tir.out" 2>&1
rc=$?

# Evidencias: saida da suite, logs e capturas do TIR (sem a config, que tem a senha). Tudo passa
# antes por uma area de preparo onde o valor da senha e trocado por *** em QUALQUER arquivo (os logs
# do proprio TIR podem registrar parametros de login).
prep="$tmp/prep"; mkdir -p "$prep"
cp "$tmp/tir.out" "$prep/tir.log"
cp -r "$tmp/log/." "$prep/" 2>/dev/null || true
cp -r "$tmp/shots/." "$prep/" 2>/dev/null || true
python - "$rel" "$prep" <<'PY' || { erro "falha ao sanear as evidencias; nada foi copiado"; exit 3; }
import os, re, sys
rel, raiz = sys.argv[1], sys.argv[2]
with open(f"/run/secrets/plab_{rel}_admin_password", "rb") as f:
    senha = f.read().strip(b"\r\n")
campo = re.compile(rb'("Password"\s*:\s*)"[^"]*"')
for pasta, _, arquivos in os.walk(raiz):
    for nome in arquivos:
        caminho = os.path.join(pasta, nome)
        with open(caminho, "rb") as f:
            dados = f.read()
        novo = campo.sub(rb'\1"***"', dados.replace(senha, b"***") if senha else dados)
        if novo != dados:
            with open(caminho, "wb") as f:
                f.write(novo)
PY
cp -r "$prep/." "$evid/"
cat "$evid/tir.log"
[ "$rc" -eq 124 ] && erro "suite excedeu o limite de tempo"
echo "resumo tir $rel: rc=$rc evidencias=$evid"
exit "$rc"
