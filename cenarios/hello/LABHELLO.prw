/*/{Protheus.doc} LABHELLO
Cenario hello do Protheus 2610 Lab: prova compilacao e execucao no ambiente de compilacao.
Simbolos usados (validados no TDN em 02/11/2026): User Function, ConOut, DToS, Date, Time, Return.
Fonte em CP1252 + CRLF. Acentuação de teste: "Olá, Protheus".
@type user function
@author daniel.montagna
@since 02/11/2026
@return character, mensagem gravada no console do AppServer
/*/
User Function LABHELLO()
    Local cMsg := "PLAB-HELLO OK " + DToS(Date()) + " " + Time()

    ConOut(cMsg)

Return cMsg
