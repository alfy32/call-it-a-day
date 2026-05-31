#Requires -Version 5.1
<#
.SYNOPSIS
    Call It a Day - instant event reporter.
    Posts a single start or end event to the server.
    Designed to complete in well under a second for use in lock/shutdown triggers.
.PARAMETER Action
    "start" or "end"
#>
param(
    [Parameter(Mandatory)]
    [ValidateSet('start', 'end')]
    [string]$Action
)

$configPath = Join-Path ([System.Environment]::GetFolderPath('ApplicationData')) 'callitaday\config.json'
if (-not (Test-Path $configPath)) { exit 0 }

try {
    $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
    if (-not $cfg.serverUrl -or -not $cfg.computerName) { exit 0 }

    $body = @{
        computer  = $cfg.computerName
        action    = $Action
        timestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
    } | ConvertTo-Json

    Invoke-RestMethod `
        -Uri         "$($cfg.serverUrl.TrimEnd('/'))/api/sync" `
        -Method      POST `
        -Body        $body `
        -ContentType 'application/json' `
        -TimeoutSec  5 | Out-Null
} catch {
    # Silent fail - if the server is unreachable the event is lost
}
