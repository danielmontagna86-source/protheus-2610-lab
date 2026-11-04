# plab.ps1 - wrapper do host para o Protheus 2610 Lab (Windows PowerShell 5.1+).
# Contrato: specs/001-protheus-2610-lab/contracts/plab-cli.md
# Uso: .\plab.ps1 <net|ports|up|down|status|logs|smoke|restart|snapshot|snapshots|restore|snapshot-rm|setup|scan> [alvo] [opcoes]

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
    return $oEnv
}

function Testar-Docker {
    & docker info --format '{{.ServerVersion}}' *> $null
    if ($LASTEXITCODE -ne 0) { Sair 3 'Docker nao respondeu. Abra o Docker Desktop.' }
}

function Arquivo-Compose([string] $cAlvo) {
    switch ($cAlvo) {
        '2610' { return Join-Path $cRaiz 'stacks\2610\compose.yaml' }
        '2510' { return Join-Path $cRaiz 'stacks\2510\compose.yaml' }
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

function Cmd-Up($oEnv, [string] $cAlvoArg) {
    Alvos $cAlvoArg | Out-Null
    Testar-Docker
    Garantir-Rede
    foreach ($cAlvo in (Alvos $cAlvoArg)) {
        Checar-Portas $oEnv $cAlvo
        if ($cAlvo -eq 'lab') {
            foreach ($cDir in 'workspace', 'evidencias') { New-Item -ItemType Directory -Force -Path (Join-Path $cRaiz $cDir) | Out-Null }
        }
        Write-Host "subindo $(Projeto $cAlvo)..."
        $nRet = Compose $cAlvo @('up', '-d', '--wait', '--wait-timeout', '900')
        if ($nRet -ne 0) { Sair 5 "$(Projeto $cAlvo) nao ficou healthy. Veja: .\plab.ps1 logs $cAlvo" }
        if ($aReleases -contains $cAlvo) { Renovar-Senha-Admin $cAlvo $oEnv }
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
    if ($cCmd -eq 'restore' -and $nRc -eq 0) { Renovar-Senha-Admin $cRel $oEnv }
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
  .\plab.ps1 snapshot <rel> [nome]     copia o volume do banco da release (para a release durante a copia)
  .\plab.ps1 snapshots <rel>           lista as copias da base
  .\plab.ps1 restore <rel> <nome>      volta a base para a copia (GRAVA no banco do lab)
  .\plab.ps1 snapshot-rm <rel> <nome>  apaga uma copia
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
    { $_ -in 'snapshot', 'restore' } { Cmd-Copia-Base (Ler-Env) $Comando $Alvo $Servico }
    { $_ -in 'snapshots', 'snapshot-rm' } { Ler-Env | Out-Null; Cmd-Copias $Comando $Alvo $Servico }
    'setup'  { Ler-Env | Out-Null; exit (Cmd-Lab @('setup') $true) }
    'scan'   { & (Join-Path $cRaiz 'lab\bin\plab-scan.ps1'); exit $LASTEXITCODE }
    default  { Ajuda; if ($Comando -ne 'help') { exit 2 } }
}
