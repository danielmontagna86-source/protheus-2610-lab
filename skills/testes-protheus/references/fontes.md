# Fontes e limites de validade

author: daniel.montagna
Consultadas em 08/10/2026. Revalidar no projeto e em novas releases.

## Primárias públicas

- [Skills Antigravity por superfície](https://antigravity.google/docs/skills?app=antigravity-ide): caminhos próprios IDE/2.0 e CLI, descoberta em nova conversa e Customizations. Não tratar Gemini CLI como Antigravity nem pasta instalada como catálogo comprovado.
- [SmartClient HTML/WebApp TOTVS](https://tdn.totvs.com/display/tec/SmartClient+HTML): diferença de cliente browser e desktop; verificar suporte/versões no alvo.
- [Poui TIR](https://totvs.github.io/tir/poui.html) e [PO UI](https://po-ui.io): suporte separado, sem assumir APIs de Webapp ou qualquer componente Angular. A skill po-ui-angular foi consultada, sem redistribuir seu corpus.

- [API Webapp oficial TIR](https://totvs.github.io/tir/webapp.html): assinaturas Webapp/config_path, Setup, Program, CheckResult, Screenshot e AssertTrue/TearDown. Também alerta sobre fragilidade de locators. O site rotulado 2.0.0 pode divergir do pacote; conferir instalação.
- [Repositório oficial TIR TOTVS](https://github.com/totvs/tir): suporte Webapp, configuração por caminho externo, orientação atual de Python 3.12 e exemplos oficiais. Não copiar instalação upgrade automática para campanhas reprodutíveis; fixar dependências compatíveis.
- [ProBat TOTVS](https://tdn.totvs.com/display/tec/PROBAT): referência de testes unitários TLPP/AdvPL. A busca oficial confirmou a página; abertura integral falhou nesta pesquisa, por isso não foi gerado exemplo de API ProBat.
- [Schedule Protheus TOTVS](https://tdn.totvs.com/display/framework/Schedule+Protheus) e [agendamento de rotinas](https://tdn.totvs.com/pages/viewpage.action?pageId=271167961): referência de agendamento/agents/monitor. Abertura integral da primeira página falhou; nenhuma tabela/status/API do Schedule foi presumida a partir de snippets.
- [CNPJ alfanumérico Receita Federal](https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/cnpj-alfanumerico): formato que admite letras; não rejeitar por somente dígitos.
- [Primeiro CNPJ alfanumérico — Receita Federal](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2026/julho/receita-federal-gera-o-primeiro-cnpj-em-formato-alfanumerico): confirma implantação em 31/07/2026. Não há necessidade de reproduzir documento cadastral real nesta skill.

## Referências locais, sem conteúdo privado exportado

[EngPro tir-test-generator](https://github.com/totvs/engpro-advpl-tlpp-skills) 5.1.0 (MIT, commit 41504805, consultada em 02/11/2026: arquitetura de três arquivos, Webapp x Poui, dual-helper, `POUILogin`/`POUI`/`NewHome`), skill-creator, writing-skills, Spec Kit, verificação antes da conclusão e orquestração foram consultadas. Autoria/licenças delas pertencem aos mantenedores; esta skill não redistribui seus arquivos nem códigos proprietários. Regras locais prevalecem sobre exemplos genéricos, e API oficial/versionada prevalece sobre dica antiga incompatível.

As lições foram generalizadas de homologações TIR com importação, agrupamento, envio, baixa, repasse e arquivo de liquidação, e de campanhas de geração com retomada. Aqui há apenas princípios e exemplos sintéticos; nenhuma cobertura, performance ou volume é afirmado a partir delas.

## O que foi e não foi validado

Testes Python deste pacote validam decisões locais com dados sintéticos, scanner e runner; não abrem ERP, Oracle ou navegador. Versão1.1.0 acrescenta gates de identificação de superfície, usuário/domínio e leitura GET protegida; GetValue foi confirmado também no código Python do pacote instalado2.14.10, sem instanciar browser. Baseline de cenários de pressão sem a nova skill já tomou decisões corretas: não houve RED comportamental observado, portanto não afirmar ganho causal da skill. RED técnico dos helpers foi observado antes da implementação. Revisão independente confere artefatos, não substitui piloto TIR do time.

Cada instalação do time precisa de piloto controlado em QA, adapter versionado e evidência integral antes de uso operacional. Não prometer ausência de falha, compatibilidade com todas as releases, cobertura financeira universal ou validade tributária de exemplos.
