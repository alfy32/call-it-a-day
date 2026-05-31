#Requires -Version 5.1
#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Call It a Day - Windows agent uninstaller.
    Removes Task Scheduler tasks and config.
#>

$CONFIG_DIR  = Join-Path $env:APPDATA "callitaday"
$CONFIG_PATH = Join-Path $CONFIG_DIR "config.json"
$TASKS       = @("CallItaDay-Logon", "CallItaDay-Unlock", "CallItaDay-End", "CallItaDay-Start")

Write-Host ""
Write-Host "Call It a Day - Windows Agent Uninstaller"
Write-Host "------------------------------------------"
Write-Host ""

# ── Remove scheduled tasks ────────────────────────────────────────────────────
foreach ($name in $TASKS) {
    if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
        Write-Host "Removed task: $name"
    }
}

# ── Remove config ─────────────────────────────────────────────────────────────
if (Test-Path $CONFIG_PATH) {
    Remove-Item -Path $CONFIG_PATH -Force
    Write-Host "Removed $CONFIG_PATH"
}

if (Test-Path $CONFIG_DIR) {
    $remaining = Get-ChildItem -Path $CONFIG_DIR -Force
    if (-not $remaining) {
        Remove-Item -Path $CONFIG_DIR -Force
        Write-Host "Removed $CONFIG_DIR"
    }
}

Write-Host ""
Write-Host "Done. The agent has been removed from this machine."
