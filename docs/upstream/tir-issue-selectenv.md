# Rascunho de issue para github.com/totvs/tir

> Status: ENVIADO em 02/11/2026 como https://github.com/totvs/tir/issues/2169 (autorizado pelo dono).

> Também reproduzido em `release/v2.14.13rc1` (commit f97e2d4, 30/10/2026), com
> `Setup("SIGAMDI", ...)`: preso em `Filling Server Environment: "P2610"` até o TimeOut, reinício
> do navegador e mesma parada. Os PRs #1955, #2155 e #2162 tratam o campo de ambiente da tela de
> sessão e o modal de confirmação, não o `#selectEnv` da tela de parâmetros iniciais.

**Título:** Setup não conclui no WebApp 26.0.0 / SmartClient HTML 10.0.2: campo de ambiente (#selectEnv) autocompleta e o valor digitado fica embaralhado

## Ambiente

- TIR 2.14.12 (PyPI), Python 3.12.3, Selenium 4.19.0, Chrome for Testing 156.0.8078.80 headless
  (Linux, container Ubuntu 24.04).
- Protheus 12.1.2610: AppServer 26.3.0.0 (build 7.00.260324P), WebApp 26.0.0, login PO UI.
- Protheus 12.1.2510: AppServer 24.3.1.1 (build 7.00.240223P), SmartClient HTML 10.0.2, login PO UI.
- `config.json`: `"Browser": "Chrome"`, `"POUI": false`, `"POUILogin": true`, `"NewHome": false`,
  `"Headless": true`, `"ChromeDriverAutoInstall": false`.

## Comportamento

`Setup("SIGAFAT", "", "99", "01", "05")` fica parado em `Filling Server Environment: "P2610"` até o
`TimeOut` e reinicia o navegador; o mesmo ocorre na 2510.

## Causa observada

O campo "Ambiente no servidor" (`#selectEnv`, `wa-combobox` com `<select>` e `<input>` no shadow DOM)
autocompleta enquanto se digita. Reproduzido com Selenium puro, digitando como o `try_send_keys`:

```
opções do <select>: ['-1', 'P2610']
input após digitar "P2610": 'P261P2610'   (select.value == 'P2610')
```

Como `fill_select_element` só sai quando o valor lido do `input` é igual ao ambiente, o laço não termina.
O mesmo vale para a 2510 (`'P251P2510'`).

## Contorno usado (extensão local)

Antes de digitar, se o `<select>` interno do `#selectEnv` tem a opção exata, selecioná-la e conferir a
pós-condição:

```python
sel.value = amb; sel.dispatchEvent(new Event('change', {bubbles: true}))
inp.value = amb; inp.dispatchEvent(new Event('input', {bubbles: true}))
```

Com isso o Setup passa do ambiente; em seguida, o clique no `wa-button` OK da `.startParameters` não
levou ao login nas nossas execuções (com Playwright, um clique com espera de acionabilidade no mesmo
botão leva ao iframe `/app-root/.../login`).

## Sugestão

Em `filling_server_environment`, quando `webapp_shadowroot()`, selecionar pelo `<select>` do
`#selectEnv` (ou limpar e digitar sem disparar o autocompletar) e só então conferir o valor.

## Reprodução mínima

Script Selenium em anexo (abre `/webapp/`, digita o ambiente no `input` interno do `#selectEnv`
caractere a caractere e imprime o valor).
