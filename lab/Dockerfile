# syntax=docker/dockerfile:1
# Imagem "lab" do Protheus 2610 Lab: TIR + Chrome headless + advpls + Node, usuario nao-root.
# Unica imagem construida pelo projeto. Nada de segredo em ARG/ENV/camadas.
# Versoes vem do .env (ver .env.example) via build args no lab/compose.yaml.

ARG UBUNTU_IMAGE=ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

# ---------------------------------------------------------------------------
# Estagio de downloads: Node, Chrome for Testing + chromedriver, @totvs/tds-ls (advpls)
# ---------------------------------------------------------------------------
FROM ${UBUNTU_IMAGE} AS downloads
ARG NODE_VERSION=22.23.4
ARG CHROME_VERSION=156.0.8078.80
ARG TDS_LS_VERSION=2.2.7
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl unzip xz-utils \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /dl
RUN curl -fsSLo node.tar.xz "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
 && curl -fsSLo SHASUMS256.txt "https://nodejs.org/dist/v${NODE_VERSION}/SHASUMS256.txt" \
 && grep " node-v${NODE_VERSION}-linux-x64.tar.xz\$" SHASUMS256.txt | sed "s#node-v${NODE_VERSION}-linux-x64.tar.xz#node.tar.xz#" | sha256sum -c - \
 && mkdir -p /opt/node && tar -xJf node.tar.xz -C /opt/node --strip-components=1
RUN base="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64" \
 && curl -fsSLo chrome.zip "$base/chrome-linux64.zip" \
 && curl -fsSLo chromedriver.zip "$base/chromedriver-linux64.zip" \
 && unzip -q chrome.zip -d /opt && mv /opt/chrome-linux64 /opt/chrome \
 && unzip -q chromedriver.zip -d /opt && mv /opt/chromedriver-linux64 /opt/chromedriver
RUN PATH="/opt/node/bin:$PATH" npm install --prefix /opt/tds-ls --no-audit --no-fund "@totvs/tds-ls@${TDS_LS_VERSION}" \
 && test -x /opt/tds-ls/node_modules/@totvs/tds-ls/bin/linux/advpls || chmod +x /opt/tds-ls/node_modules/@totvs/tds-ls/bin/linux/advpls

# ---------------------------------------------------------------------------
# Estagio final
# ---------------------------------------------------------------------------
FROM ${UBUNTU_IMAGE}
ARG TIR_VERSION=2.14.12
ARG PLAYWRIGHT_VERSION=1.64.1
ARG CHROME_VERSION=156.0.8078.80
ARG TDS_LS_VERSION=2.2.7
LABEL org.opencontainers.image.title="plab-lab" \
      org.opencontainers.image.description="Protheus 2610 Lab: TIR, Chrome headless, advpls" \
      org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    TZ=America/Sao_Paulo \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias de runtime do Chrome (Ubuntu 24.04, nomes t64), Python 3.12, git e utilitarios.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates curl git jq less nano unzip xz-utils tzdata locales procps \
      python3 python3-venv python3-dev build-essential unixodbc-dev libodbc2 libgl1 \
      fonts-liberation fonts-dejavu-core libasound2t64 libatk-bridge2.0-0t64 libatk1.0-0t64 \
      libcairo2 libcups2t64 libdbus-1-3 libdrm2 libgbm1 libglib2.0-0t64 libgtk-3-0t64 \
      libnspr4 libnss3 libpango-1.0-0 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
      libxdamage1 libxext6 libxfixes3 libxkbcommon0 libxrandr2 libxshmfence1 libvulkan1 \
      xdg-utils \
 && sed -i 's/^# *pt_BR.UTF-8/pt_BR.UTF-8/' /etc/locale.gen && locale-gen \
 && rm -rf /var/lib/apt/lists/*

COPY --from=downloads /opt/node /opt/node
COPY --from=downloads /opt/chrome /opt/chrome
COPY --from=downloads /opt/chromedriver /opt/chromedriver
COPY --from=downloads /opt/tds-ls /opt/tds-ls

# Caminhos padrao que Selenium/TIR procuram; advpls no PATH.
# google-chrome e um wrapper com --no-sandbox: como usuario nao-root dentro do container o Chrome
# aborta com "No usable sandbox!" (verificado em 2026-11-02) e o TIR nao permite passar argumentos
# ao navegador. O isolamento fica a cargo do proprio container.
RUN printf '#!/bin/sh\nexec /opt/chrome/chrome --no-sandbox "$@"\n' > /usr/bin/google-chrome \
 && chmod 0755 /usr/bin/google-chrome \
 && ln -s /usr/bin/google-chrome /usr/bin/chrome \
 && ln -s /opt/chromedriver/chromedriver /usr/bin/chromedriver \
 && ln -s /opt/tds-ls/node_modules/@totvs/tds-ls/bin/linux/advpls /usr/local/bin/advpls \
 && for b in node npm npx; do ln -s /opt/node/bin/$b /usr/local/bin/$b; done

# TIR em venv proprio (exige Python 3.12, que e o do Ubuntu 24.04).
RUN python3 -m venv /opt/lab/venv \
 && /opt/lab/venv/bin/pip install "tir_framework==${TIR_VERSION}" \
 && /opt/lab/venv/bin/python -c "import tir" \
 && /opt/lab/venv/bin/pip install "playwright==${PLAYWRIGHT_VERSION}" \
 && /opt/lab/venv/bin/python -c "import playwright.sync_api" \
 && d=$(/opt/lab/venv/bin/python -c "import tir, os; print(os.path.dirname(tir.__file__))")/technologies/core/drivers/linux \
 && mkdir -p "$d" && ln -s /opt/chromedriver/chromedriver "$d/chromedriver.exe" \
 && apt-get purge -y build-essential python3-dev unixodbc-dev && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/* /root/.cache

# A imagem base traz o usuario "ubuntu" com UID 1000; o lab usa esse UID com nome "lab".
RUN userdel -r ubuntu 2>/dev/null || true \
 && useradd -m -u 1000 -s /bin/bash lab \
 && mkdir -p /workspace /opt/plab && chown lab:lab /workspace

# Conteudo do lab (scripts, skills, templates, cenarios). Sem segredos: ver .dockerignore.
COPY --chown=root:root lab/bin/ /opt/plab/lab/bin/
COPY --chown=root:root lab/setup/ /opt/plab/lab/setup/
COPY --chown=root:root lab/tir/ /opt/plab/lab/tir/
COPY --chown=root:root lab/tests/ /opt/plab/lab/tests/
COPY --chown=root:root skills/ /opt/plab/skills/
COPY --chown=root:root templates/ /opt/plab/templates/
COPY --chown=root:root cenarios/ /opt/plab/cenarios/
RUN find /opt/plab/lab -type f \( -name '*.sh' -o -path '*/bin/*' \) -exec chmod 0755 {} + \
 && ln -s /opt/plab/lab/bin/lab /usr/local/bin/lab

ENV PATH="/opt/lab/venv/bin:/home/lab/.local/bin:/home/lab/.npm-global/bin:${PATH}" \
    PLAB_HOME=/opt/plab \
    PLAB_CHROME_VERSION=${CHROME_VERSION} \
    PLAB_TIR_VERSION=${TIR_VERSION} \
    PLAB_PLAYWRIGHT_VERSION=${PLAYWRIGHT_VERSION} \
    PLAB_CHROME_BIN=/opt/chrome/chrome \
    PLAB_TDS_LS_VERSION=${TDS_LS_VERSION}

USER lab
WORKDIR /workspace
CMD ["sleep", "infinity"]
