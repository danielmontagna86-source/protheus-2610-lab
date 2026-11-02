# plab.ps1 - wrapper do host para o Protheus 2610 Lab (Windows PowerShell 5.1+).
# Contrato: specs/001-protheus-2610-lab/contracts/plab-cli.md
# Uso: .\plab.ps1 <net|ports|up|down|status|logs|smoke|setup|scan> [alvo] [opcoes]

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
$aReleases = @('2610', '2510')

function Sair([int] $nCodigo, [string] $cMsg) {
    if ($cMsg) { [Console]::Error.WriteLine("plab: $cMsg") }
    exit $nCodigo
}

function Ler-Env {
    $cArq = Join-Path $cRaiz '.env'
    if (-not (Test-Path -LiteralPath $cArq)) {
        Sair 3 "arquivo .env ausente. Copie .env.example para .env e preencha as senhas."
    }
    $oEnv = @{}
    foreach ($cLinha in Get-Content -LiteralPath $cArq) {
        if ($cLinha -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $oEnv[$Matches[1]] = $Matches[2].Trim().Trim('"').Trim("'")
        }
    }
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

function Compose([string] $cAlvo, [string[]] $aArgs) {
    $cArq = Arquivo-Compose $cAlvo
    & docker compose --env-file (Join-Path $cRaiz '.env') -f $cArq @aArgs | Out-Host
    return $LASTEXITCODE
}

function Alvos([string] $cAlvo) {
    if ($cAlvo -eq 'all') { return $aReleases + @('lab') }
    if (-not $cAlvo) { Sair 2 'informe o alvo: 2610, 2510, lab ou all' }
    Arquivo-Compose $cAlvo | Out-Null
    return @($cAlvo)
}

function Garantir-Rede {
    & docker network inspect $cRede *> $null
    if ($LASTEXITCODE -ne 0) {
        & docker network create $cRede | Out-Null
        if ($LASTEXITCODE -ne 0) { Sair 3 "falha ao criar a rede $cRede" }
        Write-Host "rede $cRede criada"
    } else {
        Write-Host "rede $cRede ja existe"
    }
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

function Renovar-Senha-Admin([string] $cAlvo) {
    # Evita a troca obrigatoria de senha do Admin quando a base da imagem passa do prazo da
    # politica (caso da 2510, senha trocada em 12/10/2025). Nao altera a senha.
    # A credencial do banco e a padrao de desenvolvimento embutida na imagem (rede interna).
    $cSql = Join-Path $cRaiz 'stacks\sql\renova-senha-admin.sql'
    $cArq = Arquivo-Compose $cAlvo
    $aBase = @('compose', '--env-file', (Join-Path $cRaiz '.env'), '-f', $cArq)
    & docker @aBase cp $cSql 'db:/tmp/plab-renova-senha.sql' *> $null
    $cSaida = & docker @aBase exec -T -e PGPASSWORD=protheus db psql -h 127.0.0.1 -U protheus -d protheus -q -A -t -f /tmp/plab-renova-senha.sql 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Warning "renovacao da senha do Admin falhou em $(Projeto $cAlvo): $cSaida" }
    else { Write-Host "senha do Admin renovada (sem alteracao) em $(Projeto $cAlvo)" }
}

function Cmd-Up($oEnv, [string] $cAlvoArg) {
    Testar-Docker
    Garantir-Rede
    foreach ($cAlvo in (Alvos $cAlvoArg)) {
        Checar-Portas $oEnv $cAlvo
        Write-Host "subindo $(Projeto $cAlvo)..."
        $nRet = Compose $cAlvo @('up', '-d', '--wait', '--wait-timeout', '900')
        if ($nRet -ne 0) { Sair 5 "$(Projeto $cAlvo) nao ficou healthy. Veja: .\plab.ps1 logs $cAlvo" }
        if ($aReleases -contains $cAlvo) { Renovar-Senha-Admin $cAlvo }
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
    Testar-Docker
    $aArgs = @('logs', '--tail', '200')
    if ($Servico) { $aArgs += $Servico }
    Compose $cAlvoArg $aArgs | Out-Null
}

function Cmd-Lab([string[]] $aArgs, [bool] $lInterativo = $false) {
    Testar-Docker
    if (-not (Projeto-Rodando 'lab')) { Sair 3 "container lab parado. Rode: .\plab.ps1 up lab" }
    # -T (sem TTY) para comandos nao interativos; o setup precisa de terminal.
    $aBase = @('compose', '--env-file', (Join-Path $cRaiz '.env'), '-f', (Arquivo-Compose 'lab'), 'exec')
    if ($lInterativo -and -not [Console]::IsInputRedirected) {
        # "docker exec -it" direto no container: pelo "docker compose exec" chamado de dentro do
        # PowerShell 5.1 o terminal interativo nao chega ao container (verificado em 02/11/2026).
        $cId = & docker @($aBase[0..4]) ps -q lab
        & docker exec -it $cId lab @aArgs
    } else {
        & docker @aBase -T lab lab @aArgs | Out-Host
    }
    return $LASTEXITCODE
}

function Esperar-Healthy([string] $cAlvo, [string] $cServico, [int] $nSegundos = 600) {
    $cId = & docker compose --env-file (Join-Path $cRaiz '.env') -f (Arquivo-Compose $cAlvo) ps -q $cServico
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
    if ($aReleases -notcontains $cAlvo) { Sair 2 'use: restart 2610|2510' }
    Testar-Docker
    Write-Host "reiniciando o appserver de $(Projeto $cAlvo)..."
    $nRet = Compose $cAlvo @('restart', 'appserver')
    if ($nRet -ne 0) { Sair 5 "falha ao reiniciar o appserver de $(Projeto $cAlvo)" }
    # O healthcheck so passa com WebApp e /app-root respondendo.
    Start-Sleep -Seconds 20
    if (-not (Esperar-Healthy $cAlvo 'appserver')) { Sair 5 "appserver de $(Projeto $cAlvo) nao ficou healthy" }
    return (Cmd-Lab @('doctor', $cAlvo))
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
    'setup'  { Ler-Env | Out-Null; exit (Cmd-Lab @('setup') $true) }
    'scan'   { & (Join-Path $cRaiz 'lab\bin\plab-scan.ps1'); exit $LASTEXITCODE }
    default  { Ajuda; if ($Comando -ne 'help') { exit 2 } }
}
