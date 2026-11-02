-- Protheus 2610 Lab: renova a data da ultima troca de senha do Administrador (usr_id 000000)
-- SEM alterar a senha. Uso exclusivo nas bases de desenvolvimento das imagens do lab.
-- Motivo: a base da 2510 foi publicada com a senha trocada em 12/10/2025; passado o prazo da
-- politica de senha, o login exige troca obrigatoria ("Alterar senha"), o que trava o TIR em
-- toda instalacao nova. Nunca aplicar em base real.
UPDATE sys_usr
   SET usr_dtchgpsw    = to_char(current_date, 'YYYYMMDD'),
       usr_dtavichgpsw = ' '
 WHERE usr_id = '000000'
   AND d_e_l_e_t_ = ' ';
SELECT usr_id, usr_dtchgpsw, usr_dtavichgpsw FROM sys_usr WHERE usr_id = '000000';
