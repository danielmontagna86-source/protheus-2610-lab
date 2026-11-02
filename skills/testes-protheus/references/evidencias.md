# Evidência, Word e compartilhamento

author: daniel.montagna

Cada run tem pasta nova, manifesto, resultados estruturados, logs e prints próprios. Vincule teste, origem/executor, datas/horários/timezone, ambiente anonimizado no pacote externo, operações e outputs por identificadores autorizados. Evidência antiga explicitamente antiga; observação de execução externa não é ação sua. Não fabricar screenshot nem editar conteúdo para aparentar sucesso. Recortes/redações de privacidade devem ser identificados e preservar original no repositório restrito.

Word, inclusive com falhas: objetivo/escopo/versões; pré-condições; ação; esperado/observado; situação; contagens/chaves/valores/diferenças; cabeçalho/detalhes dos jobs; prints legíveis com legenda/teste; erro completo (segredos redigidos); diagnóstico sustentado; limites/pendências. Não ocultar erro por ser fora do lote: separar impacto do lote e externo, explicitando critério.

Renderize versão final DOCX em PDF/PNGs e confira todas as páginas: overflow/cortes/legendas/tabelas, sequência e legibilidade. Use skill documents quando instalada; renderer ausente = limitação, não inspeção presumida. Registre hash DOCX/PDF, contagem de páginas e quem/quando verificou. Alteração após render/revisão invalida evidência daquela versão.

Pacote de homologação: somente código útil, configuração pública, dependências/instruções, relatório final, evidências necessárias, diagnóstico e parecer. Excluir .venv, caches, backups, temporários de autenticação, configs privadas, payloads de comando e heartbeat operacional. Manifesto por caminho/hash, manter originais. Teste a cópia para detectar dependências relativas ausentes; testes não devem gerar backups de teste no ZIP.

Esta skill compartilhável contém apenas exemplos sintéticos e instruções. Não levar relatórios reais, nomes de redes/bancos, contas, CNPJ, operações ou fontes corporativos para o time sem política/autorização própria. `validate_package.py` detecta algumas classes de acidente (links locais, arquivos proibidos e padrões de segredo), mas não garante DLP completo; revisar conteúdo e metadados manualmente antes de distribuir.

Revisão independente precisa identificar versão/hashes, verificações realizadas, findings e limitações. Transporte bem-sucedido ou resposta vazia não é aprovação; recuperação técnica bounded conforme protocolo do time. Revisor indisponível: registrar aguardando validação, entregar pacote sem afirmar aceite. Não copiar token/autenticação nem contornar aprovação nativa do revisor.
