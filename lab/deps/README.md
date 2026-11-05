# Dependências travadas da imagem lab

O `lab/Dockerfile` instala o TIR, o Playwright e o `@totvs/tds-ls` (advpls) **só** a partir destes
arquivos. Cada pacote é conferido por hash:

| Arquivo | Uso no build |
|---|---|
| `requirements.lock` | `pip install --require-hashes --no-deps`: os 41 pacotes do venv, com SHA-256 |
| `requirements.in` | origem do lock: as versões exatas do venv da imagem testada (`pip freeze`) |
| `tds-ls/package.json` e `tds-ls/package-lock.json` | `npm ci`: `@totvs/tds-ls` com integridade sha512 |

O build falha se o lock não trouxer as versões de `PLAB_TIR`, `PLAB_PLAYWRIGHT` e `PLAB_TDS_LS`.

As CLIs de IA (Claude Code, Codex, opencode, Gemini) não entram na imagem: o `lab setup` as instala no
volume `lab-home`, com versão fixada no `.env.example`.

## Como gerar de novo (ao trocar a versão do TIR ou do Playwright)

1. Edite `requirements.in` com a nova versão (ou parta de um `pip freeze` de um venv já testado).
2. Gere o lock dentro da imagem lab, que é Linux, x86_64 e Python 3.12 como o build:

   ```bash
   docker run --rm -u 0 --entrypoint bash -v "$PWD/lab/deps:/out" plab-lab:local -c '
     python3 -m venv /tmp/pt && /tmp/pt/bin/pip install -q pip-tools &&
     cd /out && /tmp/pt/bin/pip-compile -q --generate-hashes --allow-unsafe --strip-extras \
       --no-header --output-file requirements.lock requirements.in'
   ```

3. Reconstrua a imagem e rode `lab smoke` nas duas releases antes de abrir o PR.

Para o `tds-ls`: troque a versão nos dois arquivos de `tds-ls/` e rode `npm install` dentro dessa
pasta, num container com Node 22, para atualizar a integridade do `package-lock.json`.
