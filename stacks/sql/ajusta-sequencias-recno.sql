-- Protheus 2610 Lab: confere (e, com -v ajustar=true, ajusta) as sequencias de R_E_C_N_O_ que
-- ficaram atrasadas na base da imagem (issue #30). Uso exclusivo nas bases de desenvolvimento
-- das imagens do lab. Nunca aplicar em base real.
-- Motivo: a chave primaria das tabelas e o R_E_C_N_O_, preenchido por nextval('<tabela>_r_e_c_n_o__seq').
-- Na base da imagem 2610, 25 de 500 tabelas tem a sequencia com o proximo valor menor ou igual ao
-- maior R_E_C_N_O_ ja gravado (sys_usr, sys_company, sys_pol_* ...): qualquer inclusao nelas cai com
-- "duplicate key value violates unique constraint". Na 2510: 0 de 493 (verificado em 07/11/2026).
-- Conta: proximo = last_value + (is_called ? 1 : 0); atrasada se proximo <= max(r_e_c_n_o_).
-- O ajuste so ADIANTA a sequencia (setval(seq, max, true): proximo = max + 1). Nao toca nos dados.
-- Saida: uma linha por tabela atrasada, "tabela|sequencia|proximo_antes|proximo_depois".
-- Variavel obrigatoria: ajustar (true = grava; false = so confere).
WITH col AS (
  SELECT c.table_schema AS s, c.table_name AS t,
         substring(c.column_default FROM 'nextval\(''([^'']+)''') AS seq
    FROM information_schema.columns c
   WHERE c.column_name = 'r_e_c_n_o_'
     AND c.column_default LIKE 'nextval(%'
     AND c.table_schema NOT IN ('pg_catalog', 'information_schema')
), v AS (
  SELECT s, t, seq,
         (xpath('/row/m/text()', query_to_xml(
            format('SELECT max(r_e_c_n_o_) AS m FROM %I.%I', s, t), false, true, '')))[1]::text::bigint AS maior,
         (xpath('/row/p/text()', query_to_xml(
            format('SELECT last_value + CASE WHEN is_called THEN 1 ELSE 0 END AS p FROM %s', seq),
            false, true, '')))[1]::text::bigint AS proximo
    FROM col
)
SELECT t, seq, proximo,
       CASE WHEN :ajustar THEN setval(seq, maior, true) + 1 ELSE maior + 1 END
  FROM v
 WHERE proximo <= maior
 ORDER BY t;
