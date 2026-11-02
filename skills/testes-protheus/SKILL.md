---
name: testes-protheus
description: Use quando planejar, implementar, executar ou revisar testes de Protheus, TIR, jobs, integrações, conciliação financeira, retomada de campanhas, evidências ou performance, inclusive homologação com grandes massas.
---

# Testes de Protheus com evidência verificável

author: daniel.montagna
Versão: 1.3.0 | Pesquisa: 02/11/2026

Produza conclusão por cenário sustentada por tela, processo e efeito de negócio. Informe aprovado, reprovado, bloqueado ou não executado; não prometa certeza absoluta. Geração de massa, compilação, teste simulado, upload e revisão documental comprovam coisas diferentes.

## Antes de executar

Leia as regras do projeto, estado anterior e autorização já fornecida. Delimite geração, importação, envio externo, baixa e liquidação: um pedido de massa não autoriza a esteira financeira. Use Spec Kit quando exigido pelo projeto e mantenha tarefas/decisões retomáveis.

Confirme ambiente em runtime e conexão de cada fonte, empresa/filial, versão de AppServer/LIB/RPO/WebApp, usuário e permissões. Não deduza a filial de um sistema integrado pela filial do ERP. Consulte fontes, menus/agendamentos, dicionário e configuração: nome de arquivo não identifica necessariamente a função; wrapper pode chamar outro comando e desencadear etapas automáticas. Leia [descoberta](references/descoberta.md).

Antes de uma mutação, verifique execuções em andamento e risco de competir com legado. Preserve os limites autorizados; produção de diagnóstico só leitura. Dados cadastrais divergentes ficam documentados, não são corrigidos automaticamente.

## Escolha do teste

| Necessidade | Referência |
|---|---|
| Tela CRUD/MVC/grid, mensagens, relatório e TIR | [Interface](references/tir.md) |
| Login/tela legado sem PO UI, browser/desktop ou renderer misto | [UI legado e PO UI](references/ui-legado-po-ui.md) |
| Jobs, importações, arquivos, chaves/valores, financeiro | [Negócio e integração](references/negocio.md) |
| Massa pequena/grande, heranças, casos negativos | [Cobertura](references/cobertura.md) |
| Máquina travada, log incompleto, retomada, concorrência | [Retomada](references/retomada.md) |
| Carga, Oracle, AppServer, baseline e regressão | [Performance](references/performance.md) |
| Prints, relatório Word, versão e pacote final | [Evidências](references/evidencias.md) |
| APIs/fontes e limites de validação desta skill | [Fontes](references/fontes.md) |

Para gerar suítes TIR, use a skill EngPro `tir-test-generator` (5.1.0 ou superior): ela define a arquitetura de três arquivos (TESTCASE, TESTSUITE, config), Webapp x Poui, o padrão dual-helper e as chaves `POUILogin`/`POUI`/`NewHome`. Esta skill define o que conta como evidência e aceite; em conflito, a API do pacote TIR instalado prevalece sobre as duas. Resumo da integração na seção "Integração EngPro" de [Interface](references/tir.md). Onde o TIR não conclui o `Setup` (WebApp 26 e SmartClient HTML 10, em 02/11/2026), complemente com Playwright conforme a seção "Complemento Playwright" da mesma referência. Testes unitários TLPP/AdvPL podem usar ProBat conforme suporte da release; esta skill não inventa chamadas. Antes de criar AdvPL/TLPP, valide símbolos no codebase/fontes padrão/exemplos/TDN e preserve CP1252; não copie fontes proprietários para o time.

## Critério comum de aceite

1. Registre pré-condições, massa exata, origem/executor, ação, início/fim com timezone, expectativa e observado.
2. Capture estado anterior quando necessário para atribuir efeitos. Sem baseline, limite a conclusão à observação posterior; não atribua geração/importação externa à suíte.
3. Confira todos os registros esperados e alcançados pela rotina, multiplicidade, exclusões justificadas, valores e vínculos. Contagens e totais iguais não detectam troca de títulos; conjuntos iguais não detectam duplicatas.
4. No monitor, correlacione cabeçalho/detalhes por processo, janela, filial, operação e identificadores de negócio. IDLOG ou status verde isolado não bastam.
5. Reexecute apenas quando autorizado e com estado anterior concluído; exija ausência dos efeitos novos que o contrato define como duplicação. Não use retry cego para tornar teste verde.
6. Falha ou parcialidade reprova a etapa. Por padrão bloqueie ações dependentes de estado incerto e continue verificações independentes. Se o usuário autorizou continuar etapas apesar de falhas, registre a política e preserve resultados negativos; isso não resolve uma mutação sem atribuição/retomada segura.

Use [manifesto](assets/manifesto.example.json), [matriz](assets/matriz.md), [caso](assets/caso.md) e [relatório](assets/relatorio.md) como adaptáveis. Exemplos são sintéticos; campos/rotinas privados não são universais TOTVS. `scripts/quality.py` fornece verificações puras, nunca acessa ERP/banco ou prova a autenticidade das entradas. Leia suas pré-condições antes de usá-lo.

## Entrega

Gere relatório inclusive com falhas, prints reais legíveis e erros completos; renderize Word e inspecione todas as páginas da versão final. Separe entregáveis de caches, backups, segredos e dados internos. Execute `python -B scripts/validate_package.py .` e os testes conforme README externo; o scanner é auxiliar, não prova ausência absoluta de segredo.

Leia as regras de revisão independente do time; configure seu revisor/interface e declare indisponibilidade quando não houver. Um transporte SUCCESS ou revisão local não substitui parecer válido ligado aos hashes da versão. Não apresente aprovação da skill como aprovação funcional do projeto ou de produção.
