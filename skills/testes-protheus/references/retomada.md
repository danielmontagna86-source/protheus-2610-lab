# Retomada segura e concorrência

author: daniel.montagna

Após falha, congelar novos disparos incertos e preservar journal/logs/checkpoints. Não apagar pending, reduzir contador nem repetir porque faltou a última linha "FIM": pode haver commit no servidor seguido de queda do cliente. Também não tomar 46 registros no log como 46 operações no banco sem reconciliação.

1. Identificar runner e árvore completa de filhos, comando/cwd/campanha, PID e criação. PID reutilizado não é o mesmo processo; pai morto não prova filho morto. Heartbeat atrasado e acesso negado não provam morte. Não matar browser/job de terceiros.
2. Exigir lock exclusivo com posse verificável, journal durável/atomic replace e baseline dos identificadores de origem. Persistir intenção antes de chamar o sistema e resultado/IDs depois. Bloqueio por falha sistêmica deve persistir e ser checado também na retomada.
3. Consultar todas as novas operações/efeitos do período e contratos relevantes, comparar com atribuídos/concluídos/pending. Contrato sozinho não identifica autoria: geração externa para mesmo contrato pode existir. SEQ inesperada, ausência de atribuição, log sem conclusão ou operação extra exigem diagnóstico; não "adotar" a operação externa nem gerar substituta para alcançar número planejado.
4. Revalidar chaves, planos/volumes, valores, estágio e views de concluídos, preservando integração já feita por outro executor. Estágio diferente do inicial pode indicar processamento externo, não ausência da geração.
5. Decidir a partir do conjunto reconciliado. Só retomar pendentes comprovados e sem worker/filho concorrente. A decisão pura em quality.py ajuda validar os conjuntos; não detecta processos, banca lock nem consulta banco, e depende de atribuição completa fornecida pelo adaptador.

Um click/disparo sem confirmação é estado incerto, não licença para repetir. Continue monitoramento/consulta e verificações independentes. Se a política autorizar seguir após falha funcional, documentar cenário e consequências, mas ainda reconciliar mutações incertas antes de nova execução.

Teste adversarial obrigatório de retomada do runner: commit sem linha final; checkpoint sem commit; filho vivo com pai morto; PID reutilizado; duas instâncias disputando lock; crash durante replace; falha sistêmica antes/depois de checkpoint; geração externa no mesmo contrato; efeito fora do plano. Mocks testam mecanismo local, não provam comportamento transacional real do ERP; runtime de crash controlado requer autorização própria.
