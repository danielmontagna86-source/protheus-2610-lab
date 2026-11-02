# Contract: `plab` (wrapper do host)

Disponível como `plab.ps1` (Windows PowerShell 5.1+) e `plab` (bash). Mesmo comportamento.

```text
plab net                      # cria a rede externa "plab" se não existir (idempotente)
plab up <2610|2510|all|lab>   # net + compose up -d --wait (timeout 900s)
plab down <alvo> [--volumes]  # compose down; --volumes pede confirmação digitando o id da release
plab status [alvo]            # estado por serviço + URLs locais
plab logs <alvo> [serviço]
plab smoke <2610|2510>        # executa "lab smoke <release>" dentro do container lab
plab setup                    # abre "lab setup" interativo no container lab
plab scan                     # varredura de segredos (git grep, docker history/inspect, logs)
plab ports                    # mostra portas configuradas e se estão livres
```

## Regras

- Lê `.env` (cópia local de `.env.example`); ausência de `.env` → erro orientando a copiar.
- Nunca aceita senha por argumento; senhas só vêm do `.env` local ou do ambiente.
- `up` recusa subir se alguma porta configurada estiver ocupada por outro processo, listando
  porta e dono (FR-004).
- `down --volumes` só afeta o project da release pedida (SC-002).
- Código de saída: 0 sucesso; 2 uso incorreto; 3 pré-requisito ausente (Docker, `.env`);
  4 porta ocupada; 5 serviço não ficou healthy; 10+ falha no smoke (ver smoke-report).
