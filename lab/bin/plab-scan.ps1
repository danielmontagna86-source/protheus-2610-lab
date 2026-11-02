# plab-scan.ps1 - varredura de segredos do Protheus 2610 Lab (Principio II / FR-023).
# Nunca imprime valores de segredo: so onde e quantas ocorrencias.
$ErrorActionPreference = 'Continue'
$cRaiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$cGitleaks = 'zricethezav/gitleaks:v8.30.1@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f'
$nFalhas = 0

function Resultado([string] $cItem, [int] $nOcorr, [string] $cDetalhe = '') {
    $cStatus = if ($nOcorr -eq 0) { 'OK    ' } else { 'FALHOU' }
    '{0} {1,-52} ocorrencias={2} {3}' -f $cStatus, $cItem, $nOcorr, $cDetalhe
    if ($nOcorr -gt 0) { $script:nFalhas++ }
}

# 1. gitleaks em todo o historico git (somente leitura; achados redigidos)
$cSaida = & docker run --rm -v "${cRaiz}:/repo:ro" $cGitleaks git /repo --redact --no-banner --exit-code 3 -v 2>&1
$nGit = ($cSaida | Select-String -Pattern '^Finding:').Count
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 3) { Resultado 'gitleaks (historico git)' 1 "falha ao executar (rc=$LASTEXITCODE)" }
else { Resultado 'gitleaks (historico git)' $nGit ($(if ($nGit) { ($cSaida | Select-String 'File:|RuleID:' | Select-Object -First 6) -join ' | ' })) }

# 2. .env.example sem valores em variaveis sensiveis
$aSens = Get-Content (Join-Path $cRaiz '.env.example') | Where-Object { $_ -match '^\s*[A-Z0-9_]*(_PASSWORD|_TOKEN|_KEY|_SECRET)\s*=\s*\S' }
Resultado '.env.example sem valores sensiveis' $aSens.Count (($aSens | ForEach-Object { ($_ -split '=')[0] }) -join ',')

# 3. Valores reais das senhas do .env local: em lugar nenhum fora do .env
$aValores = @()
$cEnv = Join-Path $cRaiz '.env'
if (Test-Path $cEnv) {
    foreach ($cLinha in Get-Content $cEnv) {
        if ($cLinha -match '^\s*[A-Z0-9_]*(_PASSWORD|_TOKEN|_KEY|_SECRET)\s*=\s*(.+)$') {
            $v = $Matches[2].Trim().Trim("'").Trim('"').Replace('$$', '$')
            if ($v.Length -ge 6) { $aValores += $v }
        }
    }
}
function Contar-Valores([string[]] $aTexto) {
    $n = 0; foreach ($v in $aValores) { $n += ($aTexto | Select-String -SimpleMatch -Pattern $v).Count }; return $n
}
Push-Location $cRaiz
$aHist = & git log --all -p --no-color 2>$null
Pop-Location
Resultado 'senhas do .env no historico git' (Contar-Valores $aHist)
$aImg = (& docker history --no-trunc plab-lab:local 2>$null) + (& docker image inspect plab-lab:local 2>$null)
Resultado 'senhas do .env na imagem plab-lab (history/inspect)' (Contar-Valores $aImg)
$cIdLab = & docker ps -q --filter 'label=com.docker.compose.project=plab-lab' --filter 'label=com.docker.compose.service=lab'
if ($cIdLab) { Resultado 'senhas do .env no inspect do container lab' (Contar-Valores (& docker inspect $cIdLab)) }
$cEvid = Join-Path $cRaiz 'evidencias'
$aEv = Get-ChildItem $cEvid -Recurse -File -Include *.log,*.json,*.out,*.txt -ErrorAction SilentlyContinue | Get-Content -ErrorAction SilentlyContinue
Resultado 'senhas do .env nas evidencias (log/json/txt)' (Contar-Valores $aEv)

# 4. Nada sensivel versionado por engano
$aRast = & git -C $cRaiz ls-files
$aProib = $aRast | Where-Object { $_ -match '(^|/)\.env$|secrets?\.env$|config\.json$|\.rpo$|\.ch$|appserver\.ini$|^evidencias/(?!\.gitkeep$)' }
Resultado 'arquivos proibidos versionados' $aProib.Count (($aProib | Select-Object -First 5) -join ',')

# 5. Evidencias (capturas/baseline locais) nunca no historico publicavel
$aHistEv = & git -C $cRaiz log --all --name-only --pretty=format: -- evidencias 2>$null | Where-Object { $_ -and $_ -notmatch '\.gitkeep$' } | Sort-Object -Unique
Resultado 'evidencias no historico git (reescrever antes de publicar)' $aHistEv.Count (($aHistEv | Select-Object -First 3) -join ',')

if ($nFalhas -gt 0) { "plab scan: $nFalhas item(ns) com ocorrencias"; exit 1 }
'plab scan: zero ocorrencias'
exit 0
