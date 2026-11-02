# UI legado, PO UI e autenticação

author: daniel.montagna

## Identificar o que realmente está aberto

Uma imagem de login cinza/branco com botão vermelho não prova renderer ou transporte. Não classificar só pela cor, logo, label "Entrar" ou campo usuário. Confirmar sessão real, versão do cliente/WebApp/LIB, conexão e contexto DOM ou identificação do executável, sem expor credenciais. O login pode usar renderer diferente das rotinas seguintes; classificar login e tela de negócio separadamente, inclusive transições/frame/aba.

| Superfície comprovada | Decisão |
|---|---|
| SmartClient HTML/WebApp no browser com rotina/widgets legado | Webapp TIR compatível com a versão; labels/GET/grid observados |
| App PO UI/Angular no browser | Adapter próprio por componente/versão; validar APIs/locators, não reutilizar widgets legado |
| WebApp com rotina que embute PO UI | Mapear ambas e troca de contexto; nenhuma classificação única implícita |
| SmartClient desktop nativo | Não dirigir com Webapp Selenium; confirmar ferramenta/suporte específico |
| Somente screenshot ou renderer incerto | Inspeção e bloqueio dos disparos incertos até mapear |

A [TOTVS diferencia WebApp e SmartClient Desktop](https://tdn.totvs.com/display/tec/SmartClient+HTML); aparência equivalente não torna transporte igual. [TIR oficial](https://github.com/totvs/tir) documenta interfaces web. Não garantir que qualquer build SmartClient desktop, WebApp antigo ou navegador seja suportado.

## Legado: GET, toolbar e grid

Rotinas AdvPL podem renderizar GET/TGet, labels e toolbars em HTML de WebApp. Esses nomes descrevem widgets/controles do projeto, não autorizam inventar classes ou APIs Python. Inspecionar atributos/label visível, contexto/modal, controles repetidos, estado disabled/read-only, foco, máscara/tamanho SX3 e linha/grid atual. Campos sem label, label distante e botões com mesmo texto exigem mapeamento explícito e match único; não assumir posição constante entre builds.

Use SetValue/SetButton/CheckResult oficiais no contrato da versão. GetValue também existe oficialmente: `GetValue(field, grid=False, line=1, grid_number=1, grid_memo_field=False, position=0)`; assinatura conferida no pacote TIR 2.14.10 e [documentação](https://totvs.github.io/tir/webapp.html#tir.main.Webapp.GetValue). Confirmar semântica de position/grid na versão; não combinar position com grid em SetValue sem contrato compatível.

Depois de digitar filtro/GET, conferir texto completo e seleção resultante: troca de foco, máscara, truncamento, espaços, refresh e tempo de trigger podem mudar conteúdo sem exception. Não desativar verificação de valor apenas para fazer teste passar. Verificar key completa do registro e reabrir consulta se necessário; isso não autoriza redisparar processamento. Em grid, enfileiramento TIR requer LoadGrid conforme documentação antes de concluir assertivas.

Fallback Selenium é restrito ao driver da sessão, seletor observado e cardinalidade/contexto verificados. Nenhum click no primeiro elemento semelhante, nenhuma alteração direta do estado interno. `ui_adapter.py` fornece gates e leitura condicionada; não detecta DOM, nem confirma versão/cardinalidade por si só. Não usar GetValue ou screenshot para ler senha, token, conta sensível ou input de autenticação preenchido.

## PO UI

A [API TIR Poui](https://totvs.github.io/tir/poui.html) existe; isso não prova suporte a qualquer componente Angular, login híbrido ou mesma assinatura Webapp. Confirmar disponibilidade no pacote instalado e contrato por método/tela. Se não houver suporte comprovado, implementar adapter Selenium/Playwright autorizado ou declarar bloqueio; não trocar de browser/driver ou ferramenta silenciosamente. Consultar skill po-ui-angular/índice e [PO UI oficial](https://po-ui.io) para seletores/inputs, sem aplicar essas regras a widgets legado.

## Login e usuário

Credenciais e domínio são configuração do ambiente, não características do layout. Usuário sem prefixo pode ser correto; domínio só quando requerido/confirmado. Não adicionar domínio corporativo por costume nem remover prefixo informado que seja necessário. `format_username` apenas monta nome sintético/configurado e rejeita conflito; não autentica e não descobre regra do ambiente.

O responsável deve confirmar ambiente e entrada de credencial pelo mecanismo autorizado. Nesta criação/instalação não houve login automático, browser ou ERP. Templates só podem autenticar quando adaptados e explicitamente autorizados no projeto; cofre/senha não entram na skill, relatório ou ZIP. Preserve login preenchido fora de prints e logs.

**Exemplo de política configurável:** um time pode aceitar em QA/teste as duas formas, simples e DOMINIO\\usuario, e exigir domínio em produção. Isso não é exigência universal TOTVS; cada time define a sua. `resolve_login_username` recebe política confirmada, chave explícita de ambiente e domínio configurado, sem domínio real no pacote.

Em QA, `as_provided` preserva usuário simples mesmo se um domínio padrão estiver configurado; `form='domain'` compõe quando escolhido e usuário já prefixado não ganha prefixo duplicado. Conflito com domínio configurado bloqueia. Em produção, ausência de domínio configurado/confirmado bloqueia inclusive nome pré-prefixado, pois prefixo sozinho não comprova domínio correto; com configuração confirmada compõe simples ou verifica prefixo. Não adivinhar domínio. Ambiente desconhecido, política não confirmada, forma conflitante ou prefixo duplicado são erros anteriores a Setup/auth.

O asset login-policy é sintético com confirmed=false: cada time confirma/adapta sua política. O smoke valida resolver e correspondência com User do config privado antes de importar/instanciar Webapp, sem gravar config/cofre ou ecoar identidade. Tests usam somente usuário/domínio fictícios e verificam que produção sem configuração não chama TIR. `format_username` sozinho é formatador genérico e não substitui esse gate de política.

## Piloto e regressão

Casos: label ausente/duplicado, modal sobreposto, foco errado, valor truncado, zero/padding/case, grid errado, trigger demorado, refresh da lista, sessão expirada, login com/sem domínio, rotina embutida POUI e renderer diferente depois do login. Testes puros/mocks verificam gates, não provam que renderer foi detectado, DOM funciona ou a sessão autenticou. Registrar versão/evidência e revalidar após atualizações.
