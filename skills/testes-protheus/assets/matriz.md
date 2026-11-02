# Matriz adaptável — exemplo sintético, não executado

author: daniel.montagna

| Caso | Massa / pré-condição | Critério / cobertura integral | Status / evidência |
|---|---|---|---|
| CT01 | CRUD/MVC válido e negativo | Persistência/chave, obrigatório, cancelamento, acesso | Não executado |
| CT02 | Importação simples e grande | Todas as chaves/valores/novos/herdados; zero extras | Não executado |
| CT03 | Multi-loja / favorecido | Origem real/documento/conta e vínculos completos | Não executado |
| CT04 | Parcial/duplicado/financeiro divergente | Falha explícita, nenhuma aprovação só por total | Não executado |
| CT05 | Job erro/timeout | Cabeçalho+detalhes e efeitos, servidor ainda ativo? | Não executado |
| CT06 | Retorno, baixa, repasse, liquidação | Status por nível, movimento real, seleção sem duplicar | Fora do escopo até autorização |
| CT07 | Reexecução concluída | Nenhum efeito novo definido como duplicação | Não executado |
| CT08 | Retomada e geração externa | Árvores/PID+criação, journal x efeitos x plano | Não executado |
| CT09 | CPF11/CNPJ14 alfanumérico | Adapter/origem correta, sem conversão destrutiva | Não executado |
| CT10 | Grandes operações e carga total | SLA/baseline, tempos separados, conciliação integral | Não executado |
| CT11 | Relatório/exportação | Filtros, chaves, totais, paginação, arquivo real | Não executado |

Adicionar variantes naturais e marcar inexistentes, não presumir cobertura. Códigos e tamanhos de negócio são definidos pelo adapter do projeto.
