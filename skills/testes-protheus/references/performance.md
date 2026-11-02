# Performance sem confundir velocidade com correção

author: daniel.montagna

Defina antes: SLA/limite de regressão, baseline comparável, hardware, versões, tamanho de massa/planos/lojas/favorecidos, warm/cold cache, concorrência preexistente, número de repetições e precisão. Sem meta acordada, apresente medidas e baseline, não "performance aprovada". Todas as chaves/valores devem conciliar na mesma execução medida; amostra rápida não aprova lote inteiro.

Separe tempo de geração no sistema de origem, SQL/banco, fila/agendador, AppServer/processamento, cliente TIR, arquivo e API externa. Medir runner que inclui conexão e validador cadastral não mede a rotina de importação/baixa nem só o banco. Timezone e clocks correlacionados; monotonic para duração local, timestamp para correlação.

Meça por operação/plano/favorecido e agregado: throughput, duração/fila, erros/timeouts, plano de execução existente, linhas, leituras lógicas/físicas, parse, memória/TEMP, CPU e esperas/locks. Mediana/p95/max exigem amostras suficientes e método de percentil declarado. Não extrapolar p95 robusto de poucas observações.

Oracle: perfis somente leitura, grants/licenciamento verificados para AWR/ASH. RAC inclui inst_id/sid/serial#, sql_id e plan_hash_value; atribuir janela e deltas com outras cargas contextualizadas. ASH é amostra, não contagem exata de chamadas; métricas cumulativas exigem deltas/reinício tratados. Consulte skills Oracle/performance disponíveis e fontes oficiais antes de query especializada. Use planos existentes via SELECT autorizado; não EXPLAIN PLAN, ALTER SESSION, coleta estatística, DDL/DML ou snapshots novos.

Não paralelizar geração/job só para benchmark se procedimento compartilha fechamento, cartão, lock ou chave e não há suporte documentado. Concorrência do aplicativo precisa de cenário/autorização separado. Cobrir idempotência completa e retomada/falha parcial pode revelar custo de reprocessar. Ausência de grants fica limitação, nunca estimativa disfarçada.
