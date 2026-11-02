# Jobs, integração e financeiro

author: daniel.montagna

Registre o contrato de cada etapa, inclusive etapas automáticas: entrada → importação → transformação/agrupamento → seleção → arquivo/remessa → recebimento → baixa → repasse → liquidação, quando fizerem parte do projeto. Não execute todas se o pedido for só gerar massa.

Monitor: capturar cabeçalho e detalhes, processo/rotina, empresa/filial, usuário, início/fim/status, operações, títulos, borderôs/remessas e erros completos. Não unir logs apenas por IDLOG; use contexto composto e janela, verificando exclusões e efeitos fora do lote. Timeout não prova que o servidor parou. Status sucesso com parcialidade é reprovado; sucesso do wrapper não prova conteúdo do processamento.

Reconcilie por chave completa de negócio (empresa/filial, operação, fornecedor+loja, prefixo, número, parcela, tipo, ou contrato do fluxo). Prefixo e tipo são campos distintos. Compare entradas, registros ERP, componentes, vínculos e arquivos com multiplicidade e valores exatos Decimal; não somente soma global. Duplicata igual nas duas fontes ainda pode ser erro: valide unicidade de negócio separadamente da comparação multiconjunto. Não deduplicar consultas silenciosamente com DISTINCT para esconder joins errados.

Valor bruto, líquido, tarifa, taxa e abatimento precisam de expressão literal do fonte/view e regra de arredondamento; não assuma "bruto - taxas = líquido" sem validar todos os componentes. Não reconstrua nominal usando coluna líquida. Strings bancárias/documentos preservam zeros e dígitos; não converta em número. Cenários por favorecido devem considerar fornecedor+loja, favorecimento/overrides e documento da origem efetiva, não só cadastro principal.

CPF é distinto de CNPJ: não preencher CPF de 11 posições com zeros para fabricar CNPJ de 14. CNPJ pode ser alfanumérico; não remover letras ou rejeitar por isdigit. Confirme máscara, dígitos verificadores e origem conforme Receita/dicionário; cadastro ausente ou ambíguo continua falha mesmo com formato válido. A skill não fornece validador tributário nem afirma que documento sintético existe.

Estado financeiro: HTTP 2xx/upload aceito prova transporte, não processamento/pagamento externo. Saldo zero/data de baixa podem nascer de agrupamento ou compensação. Correlacione retorno externo real, movimento financeiro, motivo/valor/datas e vínculo aos componentes conforme contrato. Recusado não é pago; status resumo não é status componente. Para repasse, valide elegibilidade real dos componentes e ausência de seleção dupla de resumo+componentes; para liquidação compare ativos, datas e valores contra aquisição e retorno final, distinguindo arquivo aceito de confirmação financeira.

**Customização não é padrão TOTVS:** campos customizados (prefixo X no dicionário), parâmetros próprios, status e tipos de título criados pelo projeto, bancos/códigos usados como bloqueio e regras próprias de agrupamento ou de pagamento por favorecido pertencem a adapters específicos. Não aplicar esses significados universalmente nem corrigir status por inferência de saldo/data: um status aparentemente inconsistente pode estar correto para os componentes. Leia o fonte padrão e o runtime do seu ambiente antes de definir a regra do teste.

Idempotência: snapshot antes/depois dos efeitos relevantes e de todos os registros alcançados. Reexecução não pode criar nova fatura/título/abatimento/arquivo/remessa/pagamento que o contrato considere duplicado. Arquivo sobrescrito também é impacto; hash/mtime/contador e vínculo ajudam detectar. Quando primeiro ciclo foi de outro executor, identificar autoria e limitações do baseline; estado posterior C, por exemplo, não revela quem importou.
