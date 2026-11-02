# Descoberta do ambiente e contrato

author: daniel.montagna

Antes de ações registre: release/LIB/AppServer/WebApp, identificação do RPO (quando disponível), Python/TIR/browser/driver e SO; empresa/filial/menu/usuário; fonte/conexão/schema de cada sistema; timezone e data de negócio. A informação "compilado" não prova qual RPO executa nem comportamento atual. Separe inspeção estática, build e runtime.

Resolva rotina por declaração no fonte, item real do menu e wrapper/agendamento; leia StartJob e chamadas automáticas. Uma tela pode enfileirar job e encerrar antes da execução real. Dicionários SX2/SX3/SIX/SX1/SX6 e compartilhamento de tabelas variam: não invente nome físico, chave, tamanho, índice, pergunta ou filtro. Valide APIs/signaturas no alvo antes de gerar código. CP1252 em fontes AdvPL/TLPP exige ferramenta encoding-aware; Markdown/Python desta skill são UTF-8.

Defina um adaptador por ambiente/fluxo: entidades, chave completa, origem de cada campo, expressão financeira literal, elegibilidade, statuses, junções, horários/carência, monitores e comandos. Valide identificadores SQL por allowlist/dicionário; use bind para valores. Verificação Oracle aceita apenas uma consulta SELECT/WITH sem escrita, incluindo em CTE/funções chamadas; restringir usuário a leitura é proteção adicional. Um startswith('WITH') não é guarda de segurança. Não usar NOLOCK (SQL Server), EXPLAIN PLAN, ALTER SESSION, DDL/DML ou snapshots novos em diagnóstico somente leitura.

Não compartilhe endpoints nem cadastros reais. Cada fonte precisa de origem identificada: usar o mesmo verificador alterando apenas filial pode consultar a view de outro fluxo e dar conclusão falsa. Uma filial com mecanismo diferente requer adapter próprio comprovado, inclusive joins e view que o importador efetivo lê.

Valide amostras conhecidas antes da extração integral; retorno vazio no banco errado não prova inexistência. Extração paginada precisa manter snapshot coerente ou declarar mutações entre páginas. D_E_L_E_T_ e filtro de filial são obrigatórios em tabelas de negócio Protheus onde aplicáveis; dicionários/views podem ter estrutura diferente e precisam de confirmação específica.
