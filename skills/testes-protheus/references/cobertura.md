# Cobertura orientada ao risco

author: daniel.montagna

Escolha casos pelo contrato real. Quantidade alta de operações não garante diversidade, volume por operação, payload próximo do limite nem cenários negativos. Registre matriz planejada e cobertura executada em separado; cenário ausente permanece não executado/requer massa adicional.

CRUD/MVC: inclusão/alteração/cancelamento/exclusão autorizada, obrigatórios, domínio, acesso, filial, múltiplas linhas/folders, dependências/duplicidade e concorrência pertinente. Relatório: filtros, data/vencimento, zeros/negativos, totalização, paginação e exportação.

Integração financeira: fornecedor unitário e rede multi-loja, múltiplas lojas com favorecido comum e distinto, novos versus herdados, valor zero, grandes operações, taxas/arredondamento, elegíveis/excluídos, conta/dígito/zeros, CPF e CNPJ alfanumérico da origem efetiva, cadastro ausente/ambíguo, importação antes/depois da carência configurada, parcialidade, duplicidade, divergência e job erro/timeout. Retornos aceito/recusado, agrupamento e componentização, idempotência e retomada só entram quando a etapa está autorizada.

Perfis de volume: simples, intermediário, grande validado e limite documentado do mecanismo. Não inventar limite igual para todas as filiais. Teste carga de muitas operações e grandes operações separadamente; uma mede filas/throughput, outra cardinalidade de joins/agrupamento/arquivo. Informe planos positivos novos, herdados zero e total real por operação. Se a procedure limita volume, redefinir massa com fonte validada, não forçar corrupção para atingir meta.

Geração QA usa runner específico confirmado: operações já integradas/pendentes e procedimentos que ajustam temporariamente dados precisam de autorização/registro/restauração. Nunca distribuir esses mecanismos ou credenciais nesta skill. Aqui só templates; nenhuma geração automática é incluída. Verificações SELECT/WITH não autorizam executar procedure.

Não provocar blacklist, conta inválida, recusa, cadastro faltante ou baixa incorreta em ambiente compartilhado sem autorização específica. Negativos sintéticos/mocks verificam a suíte; negativos de negócio ausentes não são marcados como exercitados. Pode-se usar erros naturais, com origem e impacto explícitos, sem atribuir a sua execução.
