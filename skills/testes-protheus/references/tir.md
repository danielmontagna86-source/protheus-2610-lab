# TIR, telas e controles

author: daniel.montagna

Use uma sessão/browser própria; preserve a sessão pessoal e mantenha visível quando o usuário quiser acompanhar. Não abra navegadores extras para observar o mesmo teste. Sessão perdida ou máquina travada exige reconciliação antes de redisparar. Para rotinas legado sem PO UI, leia [UI legado](ui-legado-po-ui.md): classificar login e tela de negócio no runtime, sem inferir renderer por screenshot. SmartClient desktop nativo não é automação Webapp.

TIR usa Webapp; testes Python com unittest devem ter TESTCASE, TESTSUITE e configuração resolvida explicitamente. `Webapp(config_path=...)` permite arquivo externo; não é obrigatório colocar segredo junto à suíte. Config pública sem senha; autenticação por mecanismo local autorizado, com config temporária protegida quando a versão exigir, removida no finally. Em CI use cofre/ACL/usuário restrito; nunca senha em argv/log/print/ZIP. Não crie prints de login preenchido. Falha na limpeza deve aparecer no resultado.

APIs mínimas confirmadas na documentação oficial consultada: `Setup(initial_program, date='', group='99', branch='01', module='')`, `Program(program_name, module='')`, `Screenshot(filename)`, `CheckResult`, `AssertTrue` e `TearDown`. A documentação online é rotulada TIR 2.0.0; valide divergências no pacote instalado, registrando versão/assinatura antes do uso. AssertTrue é agregador de verificações TIR, não prova integração; unittest verifica regras próprias. Não copie exemplos genéricos de AssertFalse para concluir que uma mensagem de erro esperada significa teste reprovado: valide a mensagem e o contrato do acumulador na sua versão.

Leia [TIR oficial](https://totvs.github.io/tir/webapp.html) e [repositório TOTVS](https://github.com/totvs/tir). Labels, chaves do browse, padding de filial, grid/linha e botões devem vir da tela real/dicionário; não extrapole outra rotina. Program busca rotina a partir do programa inicial de módulo; o módulo e a rotina efetiva precisam ser mapeados.

CRUD/MVC: inclusão válida, obrigatório/negativo, alteração persistida, cancelar sem efeito, detalhe/linhas, autorização e exclusão somente no escopo autorizado. Não presumir que ordem alfabética dos testes define uma transação; declare dependências ou use fixtures isoladas. Relatórios: valide parâmetros, filtros, entidades/linhas/valores do artefato exportado; normalização de cabeçalho/horário não pode ocultar divergência de negócio. ReportComparison tem regras próprias de normalização, confira o contrato antes de usá-lo como critério.

Retorno sem exceção de SetValue/SetButton não prova ação. Leia novamente valor completo, filtro e registro selecionado; capture contexto antes e depois. Refresh automático pode perder caracteres ou mudar linha. Aguarde condição específica, não sleep fixo como prova. Poll/timeout são parâmetros do caso; diferencie latência de disponibilidade e erro definitivo.

Quando API de alto nível falha, prefira alternativa pública TIR. Se necessário, use extensão Selenium restrita ao mesmo driver/sessão, com seletor observado, match único, elementos visíveis e pós-condição. Documente que é extensão local frágil, não API garantida TIR. Não execute JavaScript para criar resultados ou preencher diretamente estado interno do ERP. Um botão "X" pode fechar janela em vez de filtro: exija identificação e cardinalidade, nunca clique no primeiro match genérico.

## Integração EngPro tir-test-generator 5.1.0

Geração de suíte fica com a skill EngPro [tir-test-generator](https://github.com/totvs/engpro-advpl-tlpp-skills) (MIT, commit 41504805, conferida em 02/11/2026); aqui ficam aceite e evidência. Pontos que esta skill adota e não repete em outros lugares:

- Três arquivos por suíte: `{ROTINA}TESTCASE.py`, `{ROTINA}TESTSUITE.py` e config. A config com credencial é gerada em runtime em diretório temporário protegido (modo 600), com a senha vinda de variável de ambiente, e removida no finally; nunca versionada nem anexada à evidência.
- Classe: `Webapp` para MVC e browse legado; `Poui` só para telas SmartX nativas. Login, ambiente, filial e browse legado ficam sempre no helper `Webapp` (dual-helper), porque `Poui` não tem `Setup`, `SetValue`, `SetButton` nem `SetBranch`.
- Modo de interface: Protheus com login legado usa `POUI` falso e `POUILogin` falso; Protheus com login PO UI usa `POUI` falso e `POUILogin` verdadeiro; `POUI` verdadeiro é só para aplicação PO UI fora do Protheus e quebra o `Setup`. Falha logo na tela de login normalmente é essa chave trocada: confirme a tela real antes de mexer em seletor.
- `NewHome` verdadeiro quando a home após login é a de cards PO UI em vez do menu clássico; o script continua em `Webapp`. Teste preso esperando a home costuma ser essa chave.
- Navegador: o template EngPro usa Firefox; use o navegador fixado no projeto derivado (no lab conteinerizado, Chrome headless com driver da mesma versão) e registre a escolha.

Antes de usar qualquer método citado pela EngPro, confirme a assinatura no pacote TIR instalado; documentação e skill podem estar à frente ou atrás do pacote.

## Complemento Playwright (WebApp 26 e SmartClient HTML 10)

Observado em 02/11/2026 com TIR 2.14.12: o `Setup` não conclui no WebApp 26.0.0 nem no SmartClient HTML 10.0.2. O campo de ambiente autocompleta e embaralha a digitação, e o clique no botão OK da tela de parâmetros não leva ao login. Nesses ambientes, use o TIR para gerar e manter a suíte (EngPro) e complemente a execução com [Playwright para Python](https://playwright.dev/python/docs/navigations), no mesmo navegador fixado do projeto. Regras que funcionaram nos dois WebApps:

- O login PO UI e a tela de empresa/filial/módulo rodam em iframes `/app-root/.../login` e `/session-settings`. Espere o frame, não a navegação: a URL principal não muda.
- Os componentes `wa-*` guardam o rótulo no atributo `caption`, com atalho `<u>x</u>` e contador `(N)`. Localize por caption normalizado e não pelo texto visível. Com diálogos empilhados, o botão certo é o do diálogo do topo, isto é, o último visível.
- Visibilidade por área na tela: `offsetParent` é nulo dentro de diálogos fixos.
- Todo clique que fecha diálogo precisa de pós-condição (o diálogo sumiu). O controle aparece antes de estar hidratado e o primeiro clique pode não ter efeito.
- O diálogo **Moedas** do primeiro acesso do dia grava cotações ao confirmar; em teste somente leitura, use Cancelar.
- O título do browse pode diferir do nome do menu, por exemplo "Atualizacao de Produtos" para a MATA010, e a aba pode trazer a versão do programa ("Produtos [02.9.0005]"). Confira a tela real antes de fixar a expectativa.

Execução por Playwright não é API TOTVS. Registre a versão do Playwright, do navegador e do WebApp na evidência e reavalie quando o TIR corrigir o `Setup`.

## Template local

O template em assets é smoke de leitura adaptável; não foi executado em ERP. Sem config local e autorização explícita, fica skipped e o runner retorna 2, jamais verde. Uma assertiva de campo não certifica CRUD, job ou financeiro. Dependências fixadas no projeto derivado após matriz de compatibilidade, não automaticamente na versão mais recente.
