# Stored procedures: incompatibilidade e instalação

author: daniel.montagna
Pesquisa e verificação: 02/11/2026 (Protheus 12.1.2610, base de demonstração, Gestor de
Procedures "002 | 2.9.1 | TPH: OFF").

## Sintoma

Ao abrir uma rotina que usa stored procedures (ex.: FINA050 Contas a Pagar), o Protheus mostra a
janela **Incompatibilidade**:

```text
Controle 013 ref. rotina FINA050
Controle 012 ref. procedure FIN001_08_99
A stored procedure FIN001_08_99 está desatualizada.
```

A rotina não abre o browse. Isso **não é falha do teste nem da tela**: a assinatura da rotina
AdvPL (013) e a do processo instalado no banco (012) são diferentes. O TDN explica que a checagem
sempre roda e não pode ser desligada por parâmetro.

Registre como bloqueio de ambiente e não declare o cenário aprovado.

## Diagnóstico (somente leitura)

1. Anote, da janela: rotina, assinatura da rotina, procedure e assinatura da procedure.
2. O sufixo da procedure identifica processo e empresa: `FIN001_08_99` é o processo **08**
   (Somatória dos Abatimentos) na empresa **99**.
3. No banco, a tabela de controle `TOP_SP` guarda nome, assinatura (`SP_ASSINAT`), processo
   (`SP_PROCESS`) e data do pacote (`SP_DATASPS`) de cada procedure instalada:

   ```sql
   SELECT SP_NOME, SP_ASSINAT, SP_DATASPS FROM TOP_SP WHERE SP_PROCESS = '08' ORDER BY 1
   ```

4. No Configurador, **Base de Dados > Dicionário > Stored Procedure** (CFGX051M) mostra o status
   de cada processo por empresa: Atualizado, Desatualizado, Não avaliado, Não instalado ou
   **Incompatível**. Só *Incompatível* impede a rotina; *Desatualizado* funciona.

## Onde está o pacote: não precisa baixar

Desde 06/05/2022 os pacotes só saem no formato **.ZSPS, embarcados no RPO**. Eles são atualizados
pelos patches normais (Expedição Contínua), e os arquivos .SPS avulsos e o CFGX051 antigo são
obsoletos. Em ambiente sem Central de Atualizações ("TPH: OFF"), o gestor usa o pacote do RPO.

Download só é necessário quando o RPO não traz o .ZSPS do processo (status *Não avaliado*, sem
pacote no RPO). Nesse caso aplica-se o patch de Expedição Contínua Backoffice da release, obtido no
Portal de Downloads TOTVS com login de cliente. Isso é decisão do dono do ambiente.

## Instalação (grava no banco: só com autorização do dono do ambiente)

1. Garanta que ninguém está usando o processo: a instalação roda em **modo exclusivo**.
2. Entre no **SIGACFG**. No WebApp ele pode não aparecer na lista de programas iniciais; digite
   `SIGACFG` no campo. Pelo SIGAMDI com módulo 99 o login recusa ("Formulário inválido").
3. Na sessão, informe grupo e filial. Não altere a data base: mudar a data dispara o diálogo
   *Moedas*, e nele use **Cancelar**.
4. Abra **Base de Dados > Dicionário > Stored Procedure**.
5. Marque a empresa e o processo com **duplo clique** na coluna *Marca*. Um clique só seleciona a
   linha, e o gestor responde "Nenhuma empresa foi selecionada".
6. Clique em **Instalar** (primeiro botão da barra lateral) e confirme **Sim** no aviso de modo
   exclusivo.
7. Pós-condição: o *Resumo da instalação* deve ter **Falhas: 0**. Reexecutar com o processo já
   atualizado resulta em *Ignoradas*.
8. Confira `TOP_SP`: as procedures do processo precisam estar na assinatura da rotina.
9. Reabra a rotina e confira o browse.

Se continuar *Incompatível* depois de instalar, o RPO não traz a assinatura certa. A opção
**Forçar utilização de pacotes .ZSPS contidos no RPO**, nas configurações do gestor, só resolve se
o pacote do RPO tiver a mesma assinatura da rotina. Do contrário, é preciso o patch da rotina ou do
pacote.

## Resultado verificado

Protheus 12.1.2610, empresa 99, processo 08:

- antes, 11 procedures na assinatura 012 (pacote 12.1.X de 05/11/2024);
- depois, 11 procedures na assinatura 013 (pacote do RPO de 19/05/2026);
- resumo: 1 operação, 1 sucesso, 0 falhas;
- FINA050 abriu o browse com os títulos.

No Protheus 2610 Lab, o comando `lab procedures 2610 08` automatiza esses passos (Playwright). A
volta ao estado da imagem é `plab down 2610 --volumes` + `plab up 2610`.

## Cuidados

- Instalar procedures muda o banco. Em ambiente de cliente, siga a janela de manutenção e o backup
  definidos pelo dono; nunca faça isso para "fazer o teste passar" sem autorização registrada.
- Instale só os processos necessários ao cenário. Outros processos *Incompatíveis* ficam
  registrados no relatório, não corrigidos em silêncio.
- Procedures do tipo ponto de entrada podem ter customização do cliente; a desinstalação padrão não
  as remove.

## Fontes

- TDN, "Stored Procedures - Novo gerenciador de pacotes" (última alteração 09/01/2026):
  https://tdn.totvs.com/display/public/PROT/Stored+Procedures+-+Novo+gerenciador+de+pacotes
- TDN, "Stored Procedures" (visão geral): https://tdn.totvs.com/x/wi3AFQ
