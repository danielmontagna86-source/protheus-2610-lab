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
- `up` de release em `PLAB_RENOVAR_SENHA_ADMIN` renova a data da última troca de senha do Admin.
- `down --volumes` só afeta o project da release pedida (SC-002).
- Código de saída: 0 sucesso; 2 uso incorreto; 3 pré-requisito ausente (Docker, `.env`, container
  lab parado); 4 porta ocupada; 5 serviço não ficou healthy (inclui `restart`); 10+n falha no passo
  n do smoke (ver smoke-report); 15 falha no passo 5 (recuperação) do `plab smoke`.
- `scan`: 0 nenhuma ocorrência; 1 ocorrências; 2 nenhuma ocorrência, mas itens não verificados
  (imagem ausente ou container lab parado).
- `lab doctor` (dentro do container) usa a faixa 31–38: 31 DNS, 32 TCP AppServer, 33 WebApp,
  34 `/app-root`, 35 REST, 36 License Server, 37 DBAccess, 38 secret.
