# Contract: `plab` (wrapper do host)

Disponível como `plab.ps1` (Windows PowerShell 5.1+) e `plab` (bash). Mesmo comportamento.
Emenda de 2026-11-02 (achado M5): `restart`, passo 5 do smoke e códigos alinhados ao código.

```text
plab net                      # cria a rede externa "plab" se não existir (idempotente)
plab up <2610|2510|all|lab>   # net + compose up -d --wait (timeout 900s)
plab down <alvo> [--volumes]  # compose down; --volumes pede confirmação digitando o id da release
plab status [alvo]            # estado por serviço + URLs locais
plab logs <2610|2510|lab> [serviço]
plab smoke <2610|2510>        # "lab smoke <release>" no container lab (+ passo 5 de recuperação)
plab restart <2610|2510>      # reinicia só o AppServer, espera healthy e roda o doctor
plab inicializar <2610|2510>  # só fonte reserva: assistente da base vazia até a tela de login
plab snapshot <rel> [nome]    # copia o volume do Postgres da release para plab-<rel>_snap_<nome>
plab snapshots <rel>          # lista as cópias (nome, tamanho, data)
plab restore <rel> <nome>     # volta a base para a cópia (grava no banco do lab)
plab snapshot-rm <rel> <nome> # apaga uma cópia
plab setup                    # abre "lab setup" interativo no container lab
plab scan                     # varredura de segredos (git, imagem, container lab, docker logs, evidências)
plab ports                    # mostra portas configuradas e se estão livres
```

## Regras

- Lê `.env` (cópia local de `.env.example`); ausência de `.env` → erro orientando a copiar.
- O alvo é validado antes de qualquer ação; alvo ausente ou inválido → código 2.
- Nunca aceita senha por argumento; senhas só vêm do `.env` local.
- `up` recusa subir se alguma porta configurada estiver ocupada por outro processo (FR-004). O
  `plab.ps1` mostra o processo dono; o `plab` bash mostra só a porta.
- `up lab` cria `workspace/` e `evidencias/` antes de subir.
- `net`/`up` criam a rede `plab` com o label `com.plab.owner=plab`. Uma rede `plab` sem o label
  não é reutilizada (código 3), exceto a de versão anterior do plab em que todos os containers
  ligados são dos projetos `plab-*`: segue com aviso para recriar (emenda de 03/11/2026, L2).
- `up` de release em `PLAB_RENOVAR_SENHA_ADMIN` renova a data da última troca de senha do Admin.
- `PLAB_LAB_DEV=1` no `.env` (emenda de 04/11/2026): todo compose do alvo `lab` (`up`, `down`,
  `status`, `logs`, `smoke`, `setup`) recebe também `-f lab/compose.dev.yaml`, que monta `lab/`,
  `cenarios/` e `skills/` do repositório em `/opt/plab/lab`, `/opt/plab/cenarios` e
  `/opt/plab/skills` somente leitura. Ausente, vazio ou `0`: só `lab/compose.yaml` (padrão, código
  da imagem). As releases ignoram a variável. Vale no `up` seguinte (o container é recriado).
- `down --volumes` só afeta o project da release pedida (SC-002).
- `PLAB_<rel>_FONTE` (emenda de 05/11/2026, issue #3): `principal` (padrão) ou `reserva`. Qualquer
  outro valor → código 2 na leitura do `.env`.
  - Com `reserva`, os comandos da release usam `stacks/reserva/<rel>/compose.yaml`, com o mesmo
    project, as mesmas portas e volumes próprios `-reserva`.
  - `up` passa `--remove-orphans` e, depois de subir todos os alvos, roda `inicializar` em cada
    release na reserva. Se o lab estiver parado, só avisa.
  - `snapshot` e `restore` recusam a reserva com código 2.
  - A renovação da senha do Admin não roda na reserva.
- `inicializar <rel>`: código 2 se a release não está na reserva, 3 se ela está parada, 5 se o
  assistente falhou. O script vai para o container lab pela entrada padrão (bash) ou por
  `docker cp` (PowerShell, que trocaria os acentos na entrada padrão).
- `snapshot`/`restore`/`snapshots`/`snapshot-rm` (emenda de 03/11/2026): copiam o volume inteiro do
  Postgres da release (`plab-<rel>_pgdata`) para um volume `plab-<rel>_snap_<nome>` (labels
  `com.plab.owner=plab`, `com.plab.snapshot=<rel>`, `com.plab.criada`) e de volta, com
  AppServer, DBAccess e banco parados, num container auxiliar da imagem do banco sem rede. O cluster
  volta byte a byte. Não usar `CREATE DATABASE ... TEMPLATE`: em 03/11/2026 a base copiada assim fez
  o Protheus recusar o login ("O tipo do ambiente encontrado está inválido") e a 2610 precisou ser
  recriada. Nome: `a-z`, `0-9` e `_`, até 40; sem nome, o `snapshot` usa data e hora. Nome e
  existência são conferidos antes de parar a release. As cópias sobrevivem a `down --volumes`
  (são volumes à parte) e ocupam o tamanho do volume de dados. Depois de um `restore`, a release em
  `PLAB_RENOVAR_SENHA_ADMIN` tem a data da senha renovada. Códigos: 2 nome inválido, 3 release
  parada, 4 cópia inexistente ou repetida, 5 falha na cópia ou na volta da stack.
- Código de saída: 0 sucesso; 2 uso incorreto; 3 pré-requisito ausente (Docker, `.env`, container
  lab parado); 4 porta ocupada; 5 serviço não ficou healthy (inclui `restart`); 10+n falha no passo
  n do smoke (ver smoke-report); 15 falha no passo 5 (recuperação) do `plab smoke`.
- `scan`: 0 nenhuma ocorrência; 1 ocorrências; 2 nenhuma ocorrência, mas itens não verificados
  (imagem ausente ou container lab parado).
- `lab doctor` (dentro do container) usa a faixa 31–38: 31 DNS, 32 TCP AppServer, 33 WebApp,
  34 `/app-root`, 35 REST, 36 License Server, 37 DBAccess, 38 secret.
