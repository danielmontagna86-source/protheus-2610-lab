---
name: compilar-advpls-lab
description: Use quando precisar compilar fontes AdvPL/TLPP (.prw, .prx, .tlpp) no Protheus 2610 Lab, dentro do container lab, contra a release 2610 ou 2510, ou quando uma compilacao falhar com ERROR, FATAL ou COMPILEERROR-300.
---

# Compilar AdvPL/TLPP no Protheus 2610 Lab

author: daniel.montagna
Versão: 1.0.0 | 02/11/2026

## Comando

```bash
lab compile <2610|2510> caminho/fonte1.prw [caminho/fonte2.tlpp ...]
```

Compila no **ambiente de compilação** da release (`PLAB_<release>_ENV_COMPILA`): `P2610_COMPILA` na
2610 (RPO próprio, não disputa com quem usa `P2610`) e `P2510D` na 2510 (compartilha o RPO de `P2510`).

## Regras que o comando já aplica (não contorne)

1. O script do `advpls cli` é gerado em diretório temporário `0700`, arquivo `0600`, em CP1252,
   e apagado ao fim (inclusive em erro).
2. A senha vem só do secret montado em `/run/secrets/`; nunca passe senha por argumento, variável
   exportada no shell, arquivo do workspace ou log.
3. Os fontes são copiados com **nome em minúsculas** (exigência do AppServer Linux); os bytes não são
   convertidos.
4. O resultado é lido por severidade: `[SUCCESS]`, `[WARN]`, `[ERROR]`, `[FATAL]`. Um `ERROR` ou `FATAL`
   **invalida o lote inteiro**; também é falha se a quantidade de `SUCCESS` não bater com a de fontes.
5. `COMPILEERROR-300` (RPO em uso): feche as sessões abertas no ambiente de compilação — inclusive a
   sessão do TIR — e só então repita. Não force, não reinicie o AppServer sem pedir.

## Antes de compilar

- Fonte em **CP1252 + CRLF** (confira com `lab/tests/test_encoding.sh`). Nunca converta encoding em
  silêncio.
- Todo símbolo (função, classe, método) validado no TDN ou nas skills EngPro; símbolo não encontrado não
  é usado.
- Includes: os do Protheus são da TOTVS e **não** vêm no lab. Se o fonte precisar, informe um diretório
  absoluto com `PLAB_INCLUDES=/caminho` (fora do repositório) e registre de onde vieram.

## Saída e códigos

- Linha final `resumo compile <release>/<ambiente>: fontes=N SUCCESS=N WARN=N ERROR=N FATAL=N`.
- `0` ok; `2` uso (inclui nome de fonte com vírgula ou espaço e dois fontes com o mesmo nome,
  mesmo em pastas diferentes ou só com caixa diferente); `3` senha ausente; `4` includes ausentes;
  `20` compilação inválida; `21` RPO em uso; `22` senha com `$` (o `advpls cli` trava com `$` no
  `psw` — troque a senha do usuário por uma sem `$`; não tente escapar); `23` usuário ou senha com
  caractere fora do CP1252 (o script do `advpls` é gravado em CP1252).

## Limites conhecidos (verificados em 02/11/2026)

- Ordem dos includes: `PLAB_INCLUDES`, se informado; senão os da própria release no volume
  `includes-<rel>` (semeado pelo dono no host com `plab includes 2510 <pasta>`, hoje só a 2510);
  senão o volume `includes`, semeado da imagem AppServer 2610. A 1ª linha do `compile.log` diz qual
  conjunto foi usado e avisa quando a 2510 compila com os da 2610. O advpls exige escrita no
  diretório de includes e nomes em maiúsculas, por isso o comando usa uma cópia temporária.
- O advpls tenta primeiro conexão segura; o comando ignora SIGPIPE para ele cair na convencional.
- Com `PLAB_EVID_DIR` definido, grava `compile.log` (sem senha) como evidência.

## O que esta compilação não prova

Compilar com SUCCESS não prova que o fonte executa nem que a regra de negócio está correta. Para isso,
use execução no WebApp/TIR (skill `testes-protheus` + EngPro `tir-test-generator`) com evidência própria.
