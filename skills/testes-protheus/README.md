# Skill de testes Protheus para compartilhar

author: daniel.montagna

Entregável: pasta `testes-protheus` versão1.3.0 e ZIP correspondente. A 1.2.0 integra a skill EngPro `tir-test-generator` 5.1.0 como geradora de suítes; a 1.3.0 acrescenta o complemento Playwright para WebApp 26 e SmartClient HTML 10 (ver `references/tir.md`). Inclui UI legado sem PO UI, identificação de browser/desktop/renderer, GET protegido e política explícita de login por ambiente. Copie a pasta completa preservando `SKILL.md`, references, scripts, assets e tests. Não depende dos caminhos, endpoints ou credenciais do autor. Instruções não executam ERP automaticamente.

## Instalação

Codex: copie a pasta `testes-protheus` para `.codex/skills` do usuário. Claude Code: copie para `.claude/skills` do usuário, ou skills de projeto conforme mecanismo adotado pelo time. Se já existir, compare versões e preserve a antiga antes de substituir. Reabra/atualize descoberta de skills conforme cliente. Invoque `testes-protheus` ou `$testes-protheus`; seleção automática depende do suporte do cliente.

Antigravity IDE/2.0: pasta global `.gemini/config/skills/testes-protheus` no perfil; Antigravity CLI: `.gemini/antigravity-cli/skills/testes-protheus`. Alternativa por projeto: `.agents/skills/testes-protheus`. Esses caminhos são documentados para Antigravity, não deduzidos do Gemini CLI. Confira a versão do cliente e [documentação oficial](https://antigravity.google/docs/skills?app=antigravity-ide). IDE mostra skills em Customizations; CLI pode converter em `/testes-protheus`. Reabra uma sessão para atualizar descoberta e confirme catálogo. Pasta presente/hash idêntico não prova que a conversa já carregou a skill. Não alterar autenticação/hooks/permissões para forçar reconhecimento.

Outros agentes: use SKILL.md e referências como instruções do projeto, sem presumir reconhecimento de catálogo. EngPro, fontes padrão, dicionário e cofre são dependências do ambiente de trabalho, não componentes redistribuídos nesta entrega.

## Verificar a cópia sem ERP

Python padrão 3.12 ou superior para helpers. Em terminal na pasta `testes-protheus`:

```text
python -B -m unittest discover -s tests -v
python -B scripts/validate_package.py .
```

O scanner é auxiliar, não certifica ausência absoluta de segredo. Revise manualmente conteúdo e metadados. O ZIP tem manifesto/hash por arquivo e não inclui caches/backups, fontes corporativos, logs financeiros, credenciais ou casos reais identificáveis.

## Adaptar e testar em QA

1. Leia SKILL.md e referência da área do teste.
2. Defina adapter/matriz/manifesto do projeto e confirme ambiente real, comando, origem dos documentos e regras de negócio.
3. Copie assets necessários para projeto de testes isolado e substitua os exemplos sintéticos. Nenhum exemplo demonstra dado fiscal válido ou pagamento.
4. TIR: ambiente virtual Python 3.12, versões TIR/browser/driver/LIB fixadas e conferidas; consulte fontes oficiais. Templates não têm dependência instalada ou credencial.
5. Smoke de leitura: preencher configuração de caso local, comprovar rotina somente leitura e fornecer configuração TIR privada por caminho protegido. Antes, identificar runtime/login/tela de negócio conforme `references/ui-legado-po-ui.md`; print sozinho não confirma renderer. Domínio de usuário é opcional e definido pelo ambiente, sem prefixo universal. Variáveis `PROTHEUS_CASE_CONFIG`, `PROTHEUS_TIR_PRIVATE_CONFIG` e `PROTHEUS_TEST_EXECUTION_AUTHORIZED=YES` são gates de intenção, não autorização autônoma nem prova de rotina inofensiva. Execução com autorização ocorre pelo TESTSUITE adaptado. Sem adaptação o runner retorna 2/skipped. Fragmento LEGACY_READ_TEMPLATE não abre sessão ou faz login e só lê campo não sensível, com contexto/cardinalidade previamente comprovados.
6. Relatórios, SQL e critérios financeiros precisam de implementação e validação específicas; helpers puros só comparam dados fornecidos. Não há executor financeiro, gerador de massa ou conector Oracle neste pacote.

Antes de distribuir como padrão operacional, execute piloto controlado do time com CRUD/MVC, relatório e job de seu ambiente, negativos e reconciliação; registre limitações. A verificação local desta entrega não certifica todas as releases nem substitui aceite/runtime.

Exemplo de política de login configurável: QA/teste aceita usuário simples ou prefixado; produção exige domínio configurado/confirmado. Cada time define a sua; não é padrão TOTVS. No exemplo público confirmed=false exige validação pelo time. Em QA domínio padrão não força prefixo na opção simples; em produção ausência de domínio, conflito ou ambiente/política incertos bloqueiam antes de Webapp/Setup/auth. O smoke confere que User no config privado corresponde ao resolver, sem gravar esse config ou mostrar identidade. Nenhum login real foi executado nesta atualização.

Revisão final independente da versão está no workspace, fora da pasta instalável. Um parecer sobre a skill avalia artefatos/instruções, não autoriza produção. Esta entrega segue orquestrador local do autor; o time pode integrar seu próprio revisor sem transportar autenticação, hooks ou paths internos.
