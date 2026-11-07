# plab.ps1 - wrapper do host para o Protheus 2610 Lab (Windows PowerShell 5.1+).
# Contrato: specs/001-protheus-2610-lab/contracts/plab-cli.md
# Uso: .\plab.ps1 <net|ports|up|down|status|logs|smoke|restart|inicializar|snapshot|snapshots|restore|snapshot-rm|sequencias|includes|setup|scan> [alvo] [opcoes]

param(
    [Parameter(Position = 0)] [string] $Comando = 'help',
    [Parameter(Position = 1)] [string] $Alvo = '',
    [Parameter(Position = 2)] [string] $Servico = '',
    [switch] $Volumes
)

# Continue: no PowerShell 5.1, 'Stop' transforma qualquer stderr de comando nativo
# (docker) em excecao; os erros sao tratados por $LASTEXITCODE em cada chamada.
$ErrorActionPreference = 'Continue'
$cRaiz = $PSScriptRoot
$cRede = 'plab'
$cRotuloDono = 'com.plab.owner'
$aReleases = @('2610', '2510')
$lLabDev = $false  # PLAB_LAB_DEV=1 no .env (Ler-Env) liga o modo desenvolvimento do lab
$oFonte = @{}      # PLAB_<rel>_FONTE do .env (Ler-Env): principal (padrao) ou reserva
$oEnvAtual = @{}   # ultimo .env lido (Ler-Env)

function Sair([int] $nCodigo, [string] $cMsg) {
    if ($cMsg) { [Console]::Error.WriteLine("plab: $cMsg") }
    exit $nCodigo
}

function Ler-Env {
    $cArq = Join-Path $cRaiz '.env'
    if (-not (Test-Path -LiteralPath $cArq)) {
        Sair 3 "arquivo .env ausente. Copie .env.example para .env e preencha as senhas."
    }
    # Mesmas regras do plab (bash): "export " opcional, aspas simples ou duplas sem expansao e
    # comentario inline (" #") em valor sem aspas.
    $oEnv = @{}
    foreach ($cLinha in Get-Content -LiteralPath $cArq) {
        if ($cLinha -match '^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $cChave = $Matches[1]; $cValor = $Matches[2]
            if ($cValor -match '^"([^"]*)"' -or $cValor -match "^'([^']*)'") { $cValor = $Matches[1] }
            elseif ($cValor -match '^#') { $cValor = '' }
            else { $cValor = ($cValor -replace '\s#.*$', '').Trim() }
            $oEnv[$cChave] = $cValor
        }
    }
    # PLAB_LAB_DEV=1: o compose do lab soma lab\compose.dev.yaml (ver Args-Compose).
    $script:lLabDev = ($oEnv['PLAB_LAB_DEV'] -eq '1')
    $script:oEnvAtual = $oEnv  # imagens da release (Importar-Admin-Principal)
    # Fonte das imagens por release (stacks\reserva\<rel> com reserva; ver README > Fonte reserva).
    foreach ($cRel in $aReleases) {
        $cFonte = $oEnv["PLAB_${cRel}_FONTE"]
        if (-not $cFonte) { $cFonte = 'principal' }
        if ($cFonte -notin @('principal', 'reserva')) { Sair 2 "PLAB_${cRel}_FONTE invalido: '$cFonte' (use principal ou reserva)" }
        $script:oFonte[$cRel] = $cFonte
    }
    return $oEnv
}

function Testar-Docker {
    & docker info --format '{{.ServerVersion}}' *> $null
    if ($LASTEXITCODE -ne 0) { Sair 3 'Docker nao respondeu. Abra o Docker Desktop.' }
}

function Arquivo-Compose([string] $cAlvo) {
    switch ($cAlvo) {
        { $_ -in $aReleases } {
            if ($script:oFonte[$cAlvo] -eq 'reserva') { return Join-Path $cRaiz "stacks\reserva\$cAlvo\compose.yaml" }
            return Join-Path $cRaiz "stacks\$cAlvo\compose.yaml"
        }
        'lab'  { return Join-Path $cRaiz 'lab\compose.yaml' }
        default { Sair 2 "alvo invalido: '$cAlvo' (use 2610, 2510, lab ou all)" }
    }
}

function Projeto([string] $cAlvo) { return "plab-$cAlvo" }

# Argumentos do "docker compose" do alvo. No lab, PLAB_LAB_DEV=1 no .env soma lab\compose.dev.yaml:
# codigo do repositorio montado somente leitura em /opt/plab (sem rebuild da imagem).
function Args-Compose([string] $cAlvo) {
    $aArgs = @('compose', '--env-file', (Join-Path $cRaiz '.env'), '-f', (Arquivo-Compose $cAlvo))
    if ($cAlvo -eq 'lab' -and $script:lLabDev) { $aArgs += @('-f', (Join-Path $cRaiz 'lab\compose.dev.yaml')) }
    return ,$aArgs
}

function Compose([string] $cAlvo, [string[]] $aArgs) {
    $aBase = Args-Compose $cAlvo
    & docker @aBase @aArgs | Out-Host
    return $LASTEXITCODE
}

function Alvos([string] $cAlvo) {
    if ($cAlvo -eq 'all') { return $aReleases + @('lab') }
    if (-not $cAlvo) { Sair 2 'informe o alvo: 2610, 2510, lab ou all' }
    Arquivo-Compose $cAlvo | Out-Null
    return @($cAlvo)
}

# A rede e criada com o label com.plab.owner=plab e uma rede "plab" sem ele nao e reutilizada
# (Principio IV). Excecao: rede de versao anterior do plab (sem label) em que todos os containers
# ligados sao dos projetos plab-*; segue com aviso para recriar quando puder.
# Sem aspas duplas nos templates do docker: o PowerShell 5.1 nao as escapa ao chamar programas nativos.
function Garantir-Rede {
    & docker network inspect $cRede *> $null
    if ($LASTEXITCODE -ne 0) {
        & docker network create --label "$cRotuloDono=plab" $cRede | Out-Null
        if ($LASTEXITCODE -ne 0) { Sair 3 "falha ao criar a rede $cRede" }
        Write-Host "rede $cRede criada"
        return
    }
    $oRotulos = (& docker network inspect $cRede --format '{{json .Labels}}' 2>$null) | ConvertFrom-Json
    if ($oRotulos -and $oRotulos.$cRotuloDono -eq 'plab') { Write-Host "rede $cRede ja existe"; return }
    $aProjetos = @(& docker ps -a --filter "network=$cRede" --format '{{.Labels}}' 2>$null | ForEach-Object {
        if ($_ -match '(^|,)com\.docker\.compose\.project=([^,]*)') { $Matches[2] } else { '' }
    } | Sort-Object -Unique)
    $aEstranhos = @($aProjetos | Where-Object { $_ -notmatch '^plab-(2610|2510|lab)$' })
    if ($aProjetos.Count -gt 0 -and $aEstranhos.Count -eq 0) {
        Write-Warning ("a rede $cRede nao tem o label $cRotuloDono=plab (criada por versao anterior do plab). " +
            "Para recriar: .\plab.ps1 down all; docker network rm $cRede; .\plab.ps1 net")
        return
    }
    Sair 3 ("ja existe uma rede '$cRede' sem o label $cRotuloDono=plab, que o plab nao reutiliza. " +
        "Se for de outro projeto, renomeie a dele; se for de uma versao anterior do lab: docker network rm $cRede")
}

function Portas-Do-Alvo($oEnv, [string] $cAlvo) {
    $aPortas = @()
    foreach ($cChave in ($oEnv.Keys | Sort-Object)) {
        if ($cChave -like "PLAB_${cAlvo}_PORT_*") {
            $aPortas += [pscustomobject]@{ Chave = $cChave; Porta = [int] $oEnv[$cChave] }
        }
    }
    return $aPortas
}

function Dono-Porta([int] $nPorta) {
    $oCon = Get-NetTCPConnection -State Listen -LocalPort $nPorta -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $oCon) { return $null }
    $oProc = Get-Process -Id $oCon.OwningProcess -ErrorAction SilentlyContinue
    if ($oProc) { return "$($oProc.ProcessName) (pid $($oProc.Id))" }
    return "pid $($oCon.OwningProcess)"
}

function Projeto-Rodando([string] $cAlvo) {
    $cIds = & docker ps -q --filter "label=com.docker.compose.project=$(Projeto $cAlvo)"
    return [bool] $cIds
}

function Cmd-Ports($oEnv) {
    foreach ($cAlvo in $aReleases) {
        $lRodando = Projeto-Rodando $cAlvo
        foreach ($oP in (Portas-Do-Alvo $oEnv $cAlvo)) {
            $cDono = Dono-Porta $oP.Porta
            $cEstado = if (-not $cDono) { 'livre' } elseif ($lRodando) { "em uso (provavelmente plab-$cAlvo): $cDono" } else { "OCUPADA por $cDono" }
            '{0,-24} {1,6}  {2}' -f $oP.Chave, $oP.Porta, $cEstado
        }
    }
}

function Checar-Portas($oEnv, [string] $cAlvo) {
    if ($cAlvo -eq 'lab' -or (Projeto-Rodando $cAlvo)) { return }
    $aOcupadas = @()
    foreach ($oP in (Portas-Do-Alvo $oEnv $cAlvo)) {
        $cDono = Dono-Porta $oP.Porta
        if ($cDono) { $aOcupadas += "$($oP.Chave)=$($oP.Porta) ocupada por $cDono" }
    }
    if ($aOcupadas.Count -gt 0) {
        Sair 4 ("portas ocupadas; ajuste no .env:`n  " + ($aOcupadas -join "`n  "))
    }
}

function Renovar-Senha-Admin {
    # Evita a troca obrigatoria de senha do Admin quando a base da imagem passa do prazo da
    # politica (caso da 2510). Nao altera a senha; so a data da ultima troca. Decisao registrada
    # em STATUS.md e plan.md. Releases em PLAB_RENOVAR_SENHA_ADMIN (padrao 2510).
    # A senha do banco e lida dentro do container (POSTGRES_PASSWORD da imagem): nada em argv nem
    # em arquivo temporario; o SQL vai pela entrada padrao.
    param([string] $cAlvo, $oEnv)
    if ($script:oFonte[$cAlvo] -ne 'principal') { return }  # base da reserva nasce vazia, sem senha vencida
    $cLista = if ($oEnv.ContainsKey('PLAB_RENOVAR_SENHA_ADMIN')) { $oEnv['PLAB_RENOVAR_SENHA_ADMIN'] } else { '2510' }
    if (($cLista -split '[,\s]+') -notcontains $cAlvo) { return }
    $cSql = Join-Path $cRaiz 'stacks\sql\renova-senha-admin.sql'
    $aBase = Args-Compose $cAlvo
    $OutputEncoding = New-Object System.Text.UTF8Encoding $false
    # Sem aspas duplas no comando: o PowerShell 5.1 nao as escapa ao chamar programas nativos.
    # O PowerShell 5.1 poe um BOM no texto enviado a programas nativos (verificado em 03/11/2026,
    # psql: 'syntax error at or near "<BOM>"'); o sed remove o BOM dentro do container.
    $cSaida = Get-Content -Raw $cSql | & docker @aBase exec -T db sh -c 'sed 1s/^\\xEF\\xBB\\xBF// | PGPASSWORD=$POSTGRES_PASSWORD psql -h 127.0.0.1 -U postgres -d protheus -q -A -t -v ON_ERROR_STOP=1' 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Warning "renovacao da senha do Admin falhou em $(Projeto $cAlvo): $cSaida" }
    else { Write-Host "senha do Admin renovada (sem alteracao) em $(Projeto $cAlvo)" }
}

function Sequencias-Recno([string] $cAlvo, [string] $cAjustar) {
    # Sequencias de R_E_C_N_O_ atrasadas na base da imagem (issue #30). Devolve @{ Rc; Linhas; Texto }:
    # Linhas = "tabela|sequencia|antes|depois" de cada tabela atrasada. Mesmo cuidado da senha do
    # Admin: senha do banco lida dentro do container, SQL pela entrada padrao, BOM removido no sed.
    $cSql = Join-Path $cRaiz 'stacks\sql\ajusta-sequencias-recno.sql'
    $aBase = Args-Compose $cAlvo
    $OutputEncoding = New-Object System.Text.UTF8Encoding $false
    $aSaida = @(Get-Content -Raw $cSql | & docker @aBase exec -T db sh -c "sed 1s/^\\xEF\\xBB\\xBF// | PGPASSWORD=`$POSTGRES_PASSWORD psql -h 127.0.0.1 -U postgres -d protheus -q -A -t -v ON_ERROR_STOP=1 -v ajustar=$cAjustar" 2>&1)
    $nRc = $LASTEXITCODE
    $aLinhas = @($aSaida | ForEach-Object { "$_" } | Where-Object { $_ -match '^[^|\s]+\|' })
    return @{ Rc = $nRc; Linhas = $aLinhas; Texto = (($aSaida | ForEach-Object { "$_" }) -join ' ') }
}

function Ajustar-Sequencias {
    # Adianta as sequencias de R_E_C_N_O_ atrasadas ate o maior R_E_C_N_O_ gravado (issue #30: na
    # 2610 a inclusao cai com chave duplicada). Nao altera dados. Releases em
    # PLAB_AJUSTAR_SEQUENCIAS (padrao 2610). O que mudou fica em evidencias\<rel>\sequencias-<data>.txt.
    param([string] $cAlvo, $oEnv, [bool] $lForcar = $false)
    if (-not $lForcar) {
        if ($script:oFonte[$cAlvo] -ne 'principal') { return 0 }  # base da reserva e criada pelo proprio Protheus
        $cLista = if ($oEnv.ContainsKey('PLAB_AJUSTAR_SEQUENCIAS')) { $oEnv['PLAB_AJUSTAR_SEQUENCIAS'] } else { '2610' }
        if (($cLista -split '[,\s]+') -notcontains $cAlvo) { return 0 }
    }
    $oRes = Sequencias-Recno $cAlvo 'true'
    if ($oRes.Rc -ne 0) { Write-Warning "ajuste das sequencias de RECNO falhou em $(Projeto $cAlvo): $($oRes.Texto)"; return 1 }
    if ($oRes.Linhas.Count -eq 0) { Write-Host "sequencias de RECNO em dia em $(Projeto $cAlvo)"; return 0 }
    $cDir = Join-Path $cRaiz "evidencias\$cAlvo"
    New-Item -ItemType Directory -Force -Path $cDir | Out-Null
    $cArq = Join-Path $cDir ("sequencias-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.txt')
    $aTexto = @("$(Projeto $cAlvo): sequencias de R_E_C_N_O_ adiantadas em $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss') (issue #30)",
                'tabela|sequencia|proximo_antes|proximo_depois') + $oRes.Linhas
    [System.IO.File]::WriteAllText($cArq, (($aTexto -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding $false))
    Write-Host "sequencias de RECNO ajustadas em $(Projeto $cAlvo): $($oRes.Linhas.Count) tabela(s); detalhes em evidencias\$cAlvo\$(Split-Path -Leaf $cArq)"
    return 0
}

function Cmd-Sequencias($oEnv, [string] $cRel, [string] $cAcao) {
    if ($aReleases -notcontains $cRel) { Sair 2 'use: sequencias 2610|2510 [ajustar]' }
    if ($cAcao -and $cAcao -ne 'ajustar') { Sair 2 "use: sequencias $cRel [ajustar]" }
    Testar-Docker
    if (-not (Projeto-Rodando $cRel)) { Sair 3 "plab-$cRel parado. Rode: .\plab.ps1 up $cRel" }
    if ($cAcao -eq 'ajustar') {
        if ((Ajustar-Sequencias $cRel $oEnv $true) -ne 0) { Sair 5 'ajuste das sequencias falhou' }
        exit 0
    }
    $oRes = Sequencias-Recno $cRel 'false'
    if ($oRes.Rc -ne 0) { Sair 5 "conferencia das sequencias falhou: $($oRes.Texto)" }
    if ($oRes.Linhas.Count -eq 0) { Write-Host "$(Projeto $cRel): nenhuma sequencia de RECNO atrasada"; exit 0 }
    Write-Host "$(Projeto $cRel): $($oRes.Linhas.Count) sequencia(s) de RECNO atrasada(s) (nada alterado):"
    Write-Host 'tabela|sequencia|proximo|deveria_ser'
    $oRes.Linhas | ForEach-Object { Write-Host $_ }
    Write-Host "para ajustar: .\plab.ps1 sequencias $cRel ajustar"
    exit 0
}

function Cmd-Up($oEnv, [string] $cAlvoArg) {
    Alvos $cAlvoArg | Out-Null
    Testar-Docker
    Garantir-Rede
    foreach ($cAlvo in (Alvos $cAlvoArg)) {
        Checar-Portas $oEnv $cAlvo
        if ($cAlvo -eq 'lab') {
            foreach ($cDir in 'workspace', 'evidencias') { New-Item -ItemType Directory -Force -Path (Join-Path $cRaiz $cDir) | Out-Null }
        }
        if ($aReleases -contains $cAlvo) { Write-Host "subindo $(Projeto $cAlvo) (fonte $($script:oFonte[$cAlvo]))..." }
        else { Write-Host "subindo $(Projeto $cAlvo)..." }
        # --remove-orphans: ao trocar de fonte, tira o container de servico que so a outra fonte tem.
        $nRet = Compose $cAlvo @('up', '-d', '--remove-orphans', '--wait', '--wait-timeout', '900')
        if ($nRet -ne 0) { Sair 5 "$(Projeto $cAlvo) nao ficou healthy. Veja: .\plab.ps1 logs $cAlvo" }
        if ($aReleases -contains $cAlvo) { Renovar-Senha-Admin $cAlvo $oEnv; Ajustar-Sequencias $cAlvo $oEnv | Out-Null }
    }
    # Depois de todos os alvos: no "up all" o lab sobe por ultimo.
    foreach ($cAlvo in (Alvos $cAlvoArg)) {
        if ($aReleases -contains $cAlvo -and $script:oFonte[$cAlvo] -eq 'reserva') {
            if ((Inicializar-Reserva $cAlvo) -ne 0) { Write-Warning "base da reserva de $(Projeto $cAlvo) nao inicializada (veja acima)" }
        }
    }
    Cmd-Status $oEnv $cAlvoArg
}

function Cmd-Down($oEnv, [string] $cAlvoArg) {
    Testar-Docker
    foreach ($cAlvo in (Alvos $cAlvoArg)) {
        $aArgs = @('down')
        if ($Volumes) {
            $cConf = Read-Host "Isto APAGA os dados de $(Projeto $cAlvo). Digite '$cAlvo' para confirmar"
            if ($cConf -ne $cAlvo) { Write-Host "cancelado para $cAlvo"; continue }
            $aArgs += '--volumes'
        }
        $nRet = Compose $cAlvo $aArgs
        if ($nRet -ne 0) { Sair 5 "falha no down de $(Projeto $cAlvo)" }
    }
}

function Cmd-Status($oEnv, [string] $cAlvoArg) {
    Testar-Docker
    $aLista = if ($cAlvoArg) { Alvos $cAlvoArg } else { $aReleases + @('lab') }
    foreach ($cAlvo in $aLista) {
        Write-Host "== $(Projeto $cAlvo)"
        Compose $cAlvo @('ps', '--format', 'table {{.Service}}\t{{.State}}\t{{.Health}}\t{{.Ports}}') | Out-Null
        if ($aReleases -contains $cAlvo) {
            # WebApp pela porta multiprotocolo: no 26.x o /app-root (login PO UI) so existe nela.
            Write-Host ("   WebApp:  http://127.0.0.1:{0}/webapp/" -f $oEnv["PLAB_${cAlvo}_PORT_TCP"])
            Write-Host ("   TCP/TDS: 127.0.0.1:{0}   REST: http://127.0.0.1:{1}/rest/" -f $oEnv["PLAB_${cAlvo}_PORT_TCP"], $oEnv["PLAB_${cAlvo}_PORT_REST"])
        }
    }
}

function Cmd-Logs([string] $cAlvoArg) {
    if (@('2610', '2510', 'lab') -notcontains $cAlvoArg) { Sair 2 'use: logs 2610|2510|lab [servico]' }
    Testar-Docker
    $aArgs = @('logs', '--tail', '200')
    if ($Servico) { $aArgs += $Servico }
    Compose $cAlvoArg $aArgs | Out-Null
}

# Base vazia da fonte reserva, em quatro passos (o up ja chama, depois de subir todos os alvos):
#  1. assistente do Protheus ate a tela de login (empresa TESTE 99/01, Brasil);
#  2. Admin importado da base principal local da release (Importar-Admin-Principal);
#  3. Configurador: dicionario da empresa 99 criado a partir do systemload da imagem e tipo de
#     ambiente Desenvolvimento;
#  4. primeiro acesso com o Admin nos modulos do smoke e dos cenarios (dialogos do primeiro uso) e
#     Log Off. Detalhes em lab/tir/inicializar_reserva.py.
# O script e copiado para o container lab (docker cp): pela entrada padrao o PowerShell 5.1 trocaria
# os acentos que o script procura na tela. Roda antes de qualquer acesso ao /app-root/.
function Inicializar-Reserva([string] $cRel) {
    if (-not (Projeto-Rodando 'lab')) {
        Write-Warning ("container lab parado; a base da reserva ainda nao foi inicializada. " +
            "Rode .\plab.ps1 up lab e depois .\plab.ps1 inicializar $cRel, antes de qualquer outro acesso.")
        return 3
    }
    Write-Host "inicializando a base da reserva de $(Projeto $cRel) (assistente do Protheus, cerca de 3 min)..."
    $aCompose = Args-Compose 'lab'
    $cId = & docker @aCompose ps -q lab
    & docker cp (Join-Path $cRaiz 'lab\tir\inicializar_reserva.py') "${cId}:/tmp/inicializar_reserva.py" | Out-Null
    if ($LASTEXITCODE -ne 0) { return 5 }
    & docker exec $cId python -u /tmp/inicializar_reserva.py $cRel assistente | Out-Host
    if ($LASTEXITCODE -ne 0) { return $LASTEXITCODE }
    $nRc = Importar-Admin-Principal $cRel
    if ($nRc -ne 0) { return $nRc }
    Write-Host 'Configurador: dicionario a partir do systemload e tipo de ambiente (cerca de 5 min)...'
    & docker exec $cId python -u /tmp/inicializar_reserva.py $cRel configurador | Out-Host
    if ($LASTEXITCODE -ne 0) { return $LASTEXITCODE }
    Write-Host 'primeiro acesso com o Admin (modulos do smoke e dos cenarios)...'
    & docker exec $cId python -u /tmp/inicializar_reserva.py $cRel primeiro-acesso | Out-Host
    if ($LASTEXITCODE -ne 0) { return $LASTEXITCODE }
    return (Ativar-Approot-Nativo $cRel)
}

# Mesma regra do plab (bash), funcao ativar_approot_nativo: onde o compose define
# PLAB_RES_APPROOT_NATIVO=sim (2610), grava a marca de base inicializada e reinicia o appserver, que
# passa a servir o /app-root nativo. Sem aspas duplas nos argumentos (PowerShell 5.1).
function Ativar-Approot-Nativo([string] $cRel) {
    $aBase = Args-Compose $cRel
    & docker @aBase exec -T appserver sh -c 'test x$PLAB_RES_APPROOT_NATIVO = xsim' *> $null
    if ($LASTEXITCODE -ne 0) { return 0 }
    & docker @aBase exec -T appserver touch /protheus12/apo_compila/.plab-base-inicializada
    if ($LASTEXITCODE -ne 0) { return 5 }
    Write-Host "base inicializada: /app-root nativo (reiniciando o appserver de $(Projeto $cRel))..."
    & docker @aBase restart appserver *> $null
    if ($LASTEXITCODE -ne 0) { return 5 }
    Start-Sleep -Seconds 20
    if (-not (Esperar-Healthy $cRel 'appserver')) { Write-Warning "appserver de $(Projeto $cRel) nao ficou healthy"; return 5 }
    # Confere o login com o /app-root nativo (e aquece o AppServer recem-reiniciado).
    Write-Host 'conferindo o login com o /app-root nativo...'
    $aLab = Args-Compose 'lab'
    $cId = & docker @aLab ps -q lab
    & docker exec $cId python -u /tmp/inicializar_reserva.py $cRel primeiro-acesso 5 | Out-Host
    if ($LASTEXITCODE -ne 0) { return $LASTEXITCODE }
    Write-Host "$(Projeto $cRel) pronto (fonte reserva inicializada)"
    return 0
}

# Copia o registro inteiro do Admin (usr_id 000000, com senha e checksum) da base principal local da
# release para a base da reserva; mesma regra e motivo do plab (bash), funcao importar_admin_principal.
# O registro passa so por variavel e pela entrada padrao do psql (UTF-8): nunca em argumento ou arquivo.
function Importar-Admin-Principal([string] $cRel) {
    $cDados = "plab-${cRel}_pgdata"
    $cImg = $script:oEnvAtual["PLAB_${cRel}_IMG_DB"]
    & docker image inspect $cImg *> $null
    $lImagem = ($cImg -and $LASTEXITCODE -eq 0)
    if (-not (Volume-Existe $cDados) -or -not $lImagem) {
        Write-Warning ("sem base principal local da $cRel (volume $cDados e imagem $cImg); o Admin da reserva " +
            'continua sem senha. Defina-a pelo SmartClient desktop (README > Fonte reserva).')
        return 6
    }
    $cAlvo = (Select-String -Path (Join-Path $cRaiz "stacks\$cRel\compose.yaml") -Pattern '^\s*- pgdata:(.*)$' | Select-Object -First 1).Matches[0].Groups[1].Value.Trim()
    Write-Host "importando o Admin da base principal local ($cDados)..."
    $oEncSaida = [Console]::OutputEncoding; $oEncEntrada = $OutputEncoding
    $oUtf8 = New-Object System.Text.UTF8Encoding $false
    [Console]::OutputEncoding = $oUtf8; $script:OutputEncoding = $oUtf8
    try {
        $cId = & docker run -d --rm --network none --label "$cRotuloDono=plab" -v "${cDados}:$cAlvo" $cImg
        if ($LASTEXITCODE -ne 0) { return 5 }
        for ($i = 0; $i -lt 60; $i++) {
            & docker exec $cId pg_isready -q -h 127.0.0.1 *> $null
            if ($LASTEXITCODE -eq 0) { break }
            Start-Sleep -Seconds 2
        }
        # Sem aspas duplas nos argumentos: o PowerShell 5.1 as estraga ao chamar programas nativos.
        # PGPASSWORD=$POSTGRES_PASSWORD e uma atribuicao (o sh nao divide nem expande o valor); o SQL
        # vai pela entrada padrao.
        $cPsql = 'PGCLIENTENCODING=UTF8 PGPASSWORD=$POSTGRES_PASSWORD exec psql -h 127.0.0.1 -U postgres -d protheus -At -v ON_ERROR_STOP=1'
        $cSqlLer = "select row_to_json(u) from sys_usr u where usr_id = '000000' and d_e_l_e_t_ = ' ';"
        $cSqlColunas = "select column_name from information_schema.columns where table_name = 'sys_usr' order by 1;"
        $cJson = (($cSqlLer | & docker exec -i $cId sh -c $cPsql 2>$null) -join '').Trim()
        $aOrig = @($cSqlColunas | & docker exec -i $cId sh -c $cPsql 2>$null)
        & docker stop $cId *> $null
        if (-not $cJson.StartsWith('{')) { Write-Warning "Admin nao encontrado na base principal da $cRel"; return 5 }
        $aBase = Args-Compose $cRel
        $aDest = @($cSqlColunas | & docker @aBase exec -T db sh -c $cPsql)
        $aCols = @($aOrig | Where-Object { $aDest -contains $_ -and $_ -notin @('r_e_c_n_o_', 'r_e_c_d_e_l_') })
        if ($aCols.Count -eq 0) { Write-Warning "sys_usr sem colunas em comum entre as bases da $cRel"; return 5 }
        $cCols = $aCols -join ','
        $cSql = "update sys_usr t set ($cCols) = (select $cCols from json_populate_record(null::sys_usr, `$plabjson`$$cJson`$plabjson`$::json)) where t.usr_id = '000000' and t.d_e_l_e_t_ = ' ';"
        $aSaida = @($cSql | & docker @aBase exec -T db sh -c $cPsql)
        if ($aSaida -contains 'UPDATE 1') { Write-Host "Admin importado (senha igual a da base principal da $cRel)"; return 0 }
        Write-Warning "falha ao gravar o Admin na base da reserva da $cRel"
        return 5
    } finally {
        [Console]::OutputEncoding = $oEncSaida; $script:OutputEncoding = $oEncEntrada
    }
}

function Cmd-Inicializar([string] $cRel) {
    if ($aReleases -notcontains $cRel) { Sair 2 'use: inicializar 2610|2510' }
    if ($script:oFonte[$cRel] -ne 'reserva') { Sair 2 "inicializar e so para a fonte reserva (PLAB_${cRel}_FONTE=reserva)" }
    Testar-Docker
    if (-not (Projeto-Rodando $cRel)) { Sair 3 "plab-$cRel parado. Rode: .\plab.ps1 up $cRel" }
    if ((Inicializar-Reserva $cRel) -ne 0) { Sair 5 'inicializacao da base da reserva falhou (veja acima)' }
}

function Cmd-Lab([string[]] $aArgs, [bool] $lInterativo = $false) {
    Testar-Docker
    if (-not (Projeto-Rodando 'lab')) { Sair 3 "container lab parado. Rode: .\plab.ps1 up lab" }
    # -T (sem TTY) para comandos nao interativos; o setup precisa de terminal.
    $aCompose = Args-Compose 'lab'
    $aBase = $aCompose + @('exec')
    if ($lInterativo -and -not [Console]::IsInputRedirected) {
        # "docker exec -it" direto no container: pelo "docker compose exec" chamado de dentro do
        # PowerShell 5.1 o terminal interativo nao chega ao container (verificado em 02/11/2026).
        $cId = & docker @aCompose ps -q lab
        & docker exec -it $cId lab @aArgs
    } else {
        & docker @aBase -T lab lab @aArgs | Out-Host
    }
    return $LASTEXITCODE
}

function Esperar-Healthy([string] $cAlvo, [string] $cServico, [int] $nSegundos = 600) {
    $aBase = Args-Compose $cAlvo
    $cId = & docker @aBase ps -q $cServico
    $dFim = (Get-Date).AddSeconds($nSegundos)
    while ((Get-Date) -lt $dFim) {
        $cSaude = & docker inspect $cId --format '{{.State.Health.Status}}' 2>$null
        if ($cSaude -eq 'healthy') { return $true }
        Start-Sleep -Seconds 5
    }
    return $false
}

function Cmd-Restart([string] $cAlvo) {
    # Reinicia so o AppServer da release. Na 2510 e o jeito de trazer de volta o /app-root depois de
    # uma compilacao (o AppServer 24.3 religa o REST na porta do servidor interno da interface nova).
    # Retorna o codigo (nao sai) para o smoke poder reportar o passo 5.
    if ($aReleases -notcontains $cAlvo) { Sair 2 'use: restart 2610|2510' }
    Testar-Docker
    Write-Host "reiniciando o appserver de $(Projeto $cAlvo)..."
    $nRet = Compose $cAlvo @('restart', 'appserver')
    if ($nRet -ne 0) { Write-Warning "falha ao reiniciar o appserver de $(Projeto $cAlvo)"; return 5 }
    # O healthcheck so passa com WebApp e /app-root respondendo.
    Start-Sleep -Seconds 20
    if (-not (Esperar-Healthy $cAlvo 'appserver')) { Write-Warning "appserver de $(Projeto $cAlvo) nao ficou healthy"; return 5 }
    $nRet = Cmd-Lab @('doctor', $cAlvo)
    if ($nRet -ne 0) { return 5 }
    return 0
}

function Cmd-Smoke($oEnv, [string] $cAlvo) {
    if ($aReleases -notcontains $cAlvo) { Sair 2 'use: smoke 2610|2510' }
    $nRet = Cmd-Lab @('smoke', $cAlvo)
    if ($nRet -ne 0) { exit $nRet }
    $cLista = if ($oEnv.ContainsKey('PLAB_REINICIAR_APOS_COMPILAR')) { $oEnv['PLAB_REINICIAR_APOS_COMPILAR'] } else { '2510' }
    if (($cLista -split '[,\s]+') -contains $cAlvo) {
        Write-Host "[5/5] recuperacao      reiniciando appserver $cAlvo (compilacao derruba o /app-root nesta release)"
        $nRet = Cmd-Restart $cAlvo
        if ($nRet -ne 0) { Write-Host "FALHOU $cAlvo no passo 5/recuperacao"; exit 15 }
        Write-Host "[5/5] recuperacao      OK   (interface nova de volta apos a compilacao)"
    }
    exit 0
}

# Copias da base: duplicam o volume inteiro do Postgres da release (plab-<rel>_pgdata) para um
# volume plab-<rel>_snap_<nome>, com a release parada. Mesmo comportamento do plab (bash). O cluster
# volta byte a byte, inclusive a identidade interna do banco. Nao usar CREATE DATABASE ... TEMPLATE:
# em 03/11/2026 a base copiada assim fez o Protheus recusar o login ("O tipo do ambiente encontrado
# esta invalido"). A copia roda num container auxiliar da propria imagem do banco, sem rede.
$cRotuloCopia = 'com.plab.snapshot'

function Volume-Existe([string] $cVol) {
    & docker volume inspect $cVol *> $null
    return ($LASTEXITCODE -eq 0)
}

function Validar-Nome-Copia([string] $cNome) {
    if ($cNome -notmatch '^[a-z0-9_]{1,40}$') { Sair 2 "nome invalido: '$cNome' (use letras minusculas, numeros e _, ate 40)" }
}

function Copiar-Volume($oEnv, [string] $cRel, [string] $cOrigem, [string] $cDestino, [bool] $lLimpar) {
    $cImg = $oEnv["PLAB_${cRel}_IMG_DB"]
    if (-not $cImg) { Sair 3 "defina PLAB_${cRel}_IMG_DB no .env" }
    # Sem aspas duplas no comando (PowerShell 5.1 nao as escapa ao chamar programas nativos).
    $cCmd = 'cp -a /origem/. /destino/'
    if ($lLimpar) { $cCmd = 'find /destino -mindepth 1 -delete && ' + $cCmd }
    & docker run --rm --network none --entrypoint sh -v "${cOrigem}:/origem:ro" -v "${cDestino}:/destino" $cImg -c $cCmd | Out-Host
    return $LASTEXITCODE
}

function Cmd-Copia-Base($oEnv, [string] $cCmd, [string] $cRel, [string] $cNome) {
    if ($aReleases -notcontains $cRel) { Sair 2 'use: snapshot 2610|2510 [nome]  ou  restore 2610|2510 <nome>' }
    if ($cCmd -eq 'snapshot' -and -not $cNome) { $cNome = Get-Date -Format 'yyyyMMdd_HHmmss' }
    if (-not $cNome) { Sair 2 "use: restore $cRel <nome>  (copias: .\plab.ps1 snapshots $cRel)" }
    Validar-Nome-Copia $cNome
    # As copias sao do volume da base principal; na reserva o volume e outro (pgdata-reserva).
    if ($script:oFonte[$cRel] -ne 'principal') { Sair 2 "snapshot/restore so na fonte principal (PLAB_${cRel}_FONTE=reserva)" }
    Testar-Docker
    if (-not (Projeto-Rodando $cRel)) { Sair 3 "plab-$cRel parado. Rode: .\plab.ps1 up $cRel" }
    $cDados = "plab-${cRel}_pgdata"
    $cCopia = "plab-${cRel}_snap_$cNome"
    if ($cCmd -eq 'snapshot') {
        if (Volume-Existe $cCopia) { Sair 4 "ja existe a copia '$cNome' (apague antes ou use outro nome)" }
    } elseif (-not (Volume-Existe $cCopia)) {
        Sair 4 "copia '$cNome' nao existe (veja: .\plab.ps1 snapshots $cRel)"
    }
    Write-Host "parando $(Projeto $cRel) (appserver, dbaccess e banco)..."
    if ((Compose $cRel @('stop', 'appserver', 'dbaccess', 'db')) -ne 0) { Sair 5 "falha ao parar $(Projeto $cRel)" }
    $nRc = 0
    if ($cCmd -eq 'snapshot') {
        $cData = Get-Date -Format 'dd/MM/yyyy HH:mm'
        & docker volume create --label "$cRotuloDono=plab" --label "$cRotuloCopia=$cRel" --label "com.plab.criada=$cData" $cCopia | Out-Null
        if ($LASTEXITCODE -ne 0) { $nRc = 5 }
        if ($nRc -eq 0 -and (Copiar-Volume $oEnv $cRel $cDados $cCopia $false) -ne 0) { $nRc = 5 }
        if ($nRc -ne 0) { & docker volume rm $cCopia *> $null }
        else { Write-Host "copia criada: $cNome" }
    } else {
        if ((Copiar-Volume $oEnv $cRel $cCopia $cDados $true) -ne 0) { $nRc = 5 }
        else { Write-Host "base restaurada a partir da copia: $cNome" }
    }
    Write-Host "religando $(Projeto $cRel)..."
    if ((Compose $cRel @('up', '-d', '--wait', '--wait-timeout', '900')) -ne 0) { Sair 5 "$(Projeto $cRel) nao ficou healthy. Veja: .\plab.ps1 logs $cRel" }
    if ($cCmd -eq 'restore' -and $nRc -eq 0) { Renovar-Senha-Admin $cRel $oEnv; Ajustar-Sequencias $cRel $oEnv | Out-Null }
    if ($nRc -ne 0) { Sair $nRc 'falha na copia do volume; a release foi religada' }
    Write-Host "$(Projeto $cRel) pronto."
    exit 0
}

function Cmd-Copias([string] $cCmd, [string] $cRel, [string] $cNome) {
    if ($aReleases -notcontains $cRel) { Sair 2 'use: snapshots 2610|2510  ou  snapshot-rm 2610|2510 <nome>' }
    Testar-Docker
    if ($cCmd -eq 'snapshots') {
        foreach ($cVol in (& docker volume ls -q --filter "label=$cRotuloCopia=$cRel")) {
            # Sem aspas duplas no --format: o PowerShell 5.1 as remove ao chamar o docker (o
            # template quebrava com 'function "com" not defined', visto em 04/11/2026).
            $oRotulos = (& docker volume inspect $cVol --format '{{json .Labels}}') | ConvertFrom-Json
            $cData = $oRotulos.'com.plab.criada'
            Write-Host ('{0,-30} {1}' -f ($cVol -replace "^plab-${cRel}_snap_", ''), $cData)
        }
        exit 0
    }
    if (-not $cNome) { Sair 2 "use: snapshot-rm $cRel <nome>" }
    Validar-Nome-Copia $cNome
    $cCopia = "plab-${cRel}_snap_$cNome"
    if (-not (Volume-Existe $cCopia)) { Sair 4 "copia '$cNome' nao existe" }
    & docker volume rm $cCopia | Out-Null
    if ($LASTEXITCODE -ne 0) { Sair 5 "falha ao apagar a copia '$cNome'" }
    Write-Host "copia apagada: $cNome"
    exit 0
}

# Includes da TOTVS NAO vem no repositorio nem nas imagens da 2510: o usuario aponta uma pasta
# sua (ex.: os includes do pacote de fontes padrao da release) e eles vao para o volume local
# plab-lab_includes-<rel>, montado somente leitura no lab. Nada e versionado.
function Cmd-Includes([string] $cRel, [string] $cDir) {
    if ($cRel -ne '2510') { Sair 2 'use: includes 2510 <pasta-com-os-.ch> (a 2610 usa os includes da propria imagem)' }
    if (-not $cDir -or -not (Test-Path -LiteralPath $cDir -PathType Container)) { Sair 2 "pasta nao encontrada: '$cDir'" }
    if (-not (Get-ChildItem -LiteralPath $cDir -Filter 'prtopdef.ch' -File)) {
        Sair 4 'a pasta nao tem PRTOPDEF.CH: nao parece um diretorio de includes do Protheus'
    }
    Testar-Docker
    & docker image inspect plab-lab:local *> $null
    if ($LASTEXITCODE -ne 0) { Sair 3 "imagem plab-lab:local ausente: rode '.\plab.ps1 up lab' antes" }
    $cVol = "plab-lab_includes-$cRel"
    if (-not (Volume-Existe $cVol)) {
        & docker volume create --label com.docker.compose.project=plab-lab --label "com.docker.compose.volume=includes-$cRel" $cVol | Out-Null
    }
    & docker run --rm --network none --user 0 -v "${cVol}:/dst" --entrypoint bash plab-lab:local -c 'find /dst -mindepth 1 -delete'
    if ($LASTEXITCODE -ne 0) { Sair 5 "falha ao limpar o volume $cVol" }
    $cId = & docker create --network none --user 0 -v "${cVol}:/dst" --entrypoint bash plab-lab:local /tmp/includes-semear.sh /dst
    if ($LASTEXITCODE -ne 0) { Sair 5 'falha ao criar o container auxiliar' }
    $cOrigem = (Resolve-Path -LiteralPath $cDir).ProviderPath.TrimEnd('\') + '\.'
    $cScript = Join-Path $cRaiz 'lab\bin\lib\includes-semear.sh'
    $lOk = $false
    & docker cp $cOrigem "${cId}:/dst/" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        & docker cp $cScript "${cId}:/tmp/includes-semear.sh" | Out-Null
        if ($LASTEXITCODE -eq 0) { & docker start -a $cId; $lOk = ($LASTEXITCODE -eq 0) }
    }
    & docker rm -f $cId *> $null
    if (-not $lOk) { Sair 5 "falha ao copiar os includes para $cVol" }
    Write-Host "includes da $cRel prontos no volume $cVol. Se o lab estava no ar: .\plab.ps1 up lab"
    exit 0
}

function Ajuda {
    @'
plab - Protheus 2610 Lab
  .\plab.ps1 net                       cria a rede "plab" (idempotente)
  .\plab.ps1 ports                     portas configuradas e se estao livres
  .\plab.ps1 up <2610|2510|lab|all>    sobe e aguarda healthy
  .\plab.ps1 down <alvo> [-Volumes]    derruba (com -Volumes apaga dados, pede confirmacao)
  .\plab.ps1 status [alvo]             estado e URLs
  .\plab.ps1 logs <alvo> [servico]
  .\plab.ps1 smoke <2610|2510>         smoke dentro do container lab
  .\plab.ps1 restart <2610|2510>       reinicia o AppServer e roda o doctor
  .\plab.ps1 inicializar <2610|2510>   fonte reserva: inicializa a base vazia (empresa TESTE 99/01)
  .\plab.ps1 snapshot <rel> [nome]     copia o volume do banco da release (para a release durante a copia)
  .\plab.ps1 snapshots <rel>           lista as copias da base
  .\plab.ps1 restore <rel> <nome>      volta a base para a copia (GRAVA no banco do lab)
  .\plab.ps1 snapshot-rm <rel> <nome>  apaga uma copia
  .\plab.ps1 sequencias <rel> [ajustar] confere (ou ajusta) as sequencias de RECNO atrasadas (issue #30)
  .\plab.ps1 includes 2510 <pasta>    copia os includes (.ch) da sua pasta para o lab (nao versiona)
  .\plab.ps1 setup                     assistente "lab setup"
  .\plab.ps1 scan                      varredura de segredos
'@
}

switch ($Comando) {
    'net'    { Testar-Docker; Garantir-Rede }
    'ports'  { Cmd-Ports (Ler-Env) }
    'up'     { Cmd-Up (Ler-Env) $Alvo }
    'down'   { Cmd-Down (Ler-Env) $Alvo }
    'status' { Cmd-Status (Ler-Env) $Alvo }
    'logs'   { Ler-Env | Out-Null; Cmd-Logs $Alvo }
    'smoke'  { Cmd-Smoke (Ler-Env) $Alvo }
    'restart' { Ler-Env | Out-Null; exit (Cmd-Restart $Alvo) }
    'inicializar' { Ler-Env | Out-Null; Cmd-Inicializar $Alvo }
    { $_ -in 'snapshot', 'restore' } { Cmd-Copia-Base (Ler-Env) $Comando $Alvo $Servico }
    { $_ -in 'snapshots', 'snapshot-rm' } { Ler-Env | Out-Null; Cmd-Copias $Comando $Alvo $Servico }
    'sequencias' { Cmd-Sequencias (Ler-Env) $Alvo $Servico }
    'includes' { Ler-Env | Out-Null; Cmd-Includes $Alvo $Servico }
    'setup'  { Ler-Env | Out-Null; exit (Cmd-Lab @('setup') $true) }
    'scan'   { & (Join-Path $cRaiz 'lab\bin\plab-scan.ps1'); exit $LASTEXITCODE }
    default  { Ajuda; if ($Comando -ne 'help') { exit 2 } }
}
