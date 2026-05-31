#Requires -Version 5.1
<#
.SYNOPSIS
    Call It a Day - instant event reporter.
    Posts a start or end event to the server.
    Designed to complete in well under a second for use in lock/shutdown triggers.
.PARAMETER Action
    "start"  - begin a session
    "end"    - close the current session
    "logon"  - post end then start; used on boot logon to recover any session
               that was orphaned if the previous shutdown end event was missed
#>
param(
    [Parameter(Mandatory)]
    [ValidateSet('start', 'end', 'logon')]
    [string]$Action
)

$configPath = Join-Path ([System.Environment]::GetFolderPath('ApplicationData')) 'callitaday\config.json'
if (-not (Test-Path $configPath)) { exit 0 }

try {
    $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
    if (-not $cfg.serverUrl -or -not $cfg.computerName) { exit 0 }

    function Post-Event($action) {
        $body = @{
            computer  = $cfg.computerName
            action    = $action
            timestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
        } | ConvertTo-Json
        Invoke-RestMethod `
            -Uri         "$($cfg.serverUrl.TrimEnd('/'))/api/sync" `
            -Method      POST `
            -Body        $body `
            -ContentType 'application/json' `
            -TimeoutSec  5 | Out-Null
    }

    if ($Action -eq 'logon') {
        # Close any orphaned session from a missed shutdown, then start fresh.
        # The end is best-effort — no_active_session is fine.
        try { Post-Event 'end' } catch {}
        Post-Event 'start'
    } else {
        Post-Event $Action
    }
} catch {
    # Silent fail - if the server is unreachable the event is lost
}
