#Requires -Version 5.1
#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Call It a Day - Windows agent installer.
    Sets up config and registers Task Scheduler tasks.
#>

$SCRIPT_DIR    = Split-Path -Parent (Resolve-Path $MyInvocation.MyCommand.Path)
$REPORT_PS1    = Join-Path $SCRIPT_DIR "report-event.ps1"
$CONFIG_DIR    = Join-Path $env:APPDATA "callitaday"
$CONFIG_PATH   = Join-Path $CONFIG_DIR "config.json"
$TASK_LOGON    = "CallItaDay-Logon"
$TASK_UNLOCK   = "CallItaDay-Unlock"
$TASK_END      = "CallItaDay-End"

# Load existing config for re-run UX
$currentUrl  = ""
$currentName = ""
if (Test-Path $CONFIG_PATH) {
    $existing    = Get-Content $CONFIG_PATH -Raw | ConvertFrom-Json
    $currentUrl  = $existing.serverUrl
    $currentName = $existing.computerName
}
$defaultName = if ($currentName) { $currentName } else { $env:COMPUTERNAME }

# Prompts
Write-Host ""
Write-Host "Call It a Day - Windows Agent Installer"
Write-Host "----------------------------------------"
Write-Host ""

if ($currentUrl) {
    $inputUrl  = Read-Host "Server URL [$currentUrl]"
    $serverUrl = if ($inputUrl) { $inputUrl } else { $currentUrl }
} else {
    $serverUrl = Read-Host "Server URL (e.g. http://192.168.1.10:8001)"
}

$inputName    = Read-Host "Computer name [$defaultName]"
$computerName = if ($inputName) { $inputName } else { $defaultName }

if (-not $serverUrl) {
    Write-Error "Server URL cannot be empty."; exit 1
}
if ($computerName -match '\s') {
    Write-Error "Computer name cannot contain spaces."; exit 1
}

# Write config
New-Item -ItemType Directory -Force -Path $CONFIG_DIR | Out-Null
@{ serverUrl = $serverUrl.TrimEnd('/'); computerName = $computerName } |
    ConvertTo-Json | Set-Content -Path $CONFIG_PATH -Encoding UTF8
Write-Host "Wrote $CONFIG_PATH"

# --- Task: CallItaDay-Logon ---
# Fires on first logon after boot. Posts end then start so any session
# orphaned by a missed shutdown end event is closed before starting fresh.
$logonTaskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Call It a Day - post start event on logon</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT1M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions>
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-NoProfile -WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -File "$REPORT_PS1" -Action start</Arguments>
    </Exec>
  </Actions>
</Task>
"@

# --- Task: CallItaDay-Unlock ---
# Fires on screen unlock. Just posts start — the end was already recorded on lock.
$unlockTaskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Call It a Day - post start event on screen unlock</Description>
  </RegistrationInfo>
  <Triggers>
    <SessionStateChangeTrigger>
      <Enabled>true</Enabled>
      <StateChange>SessionUnlock</StateChange>
    </SessionStateChangeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT1M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions>
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-NoProfile -WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -File "$REPORT_PS1" -Action start</Arguments>
    </Exec>
  </Actions>
</Task>
"@

# --- Task: CallItaDay-End ---
# Fires on screen lock, user logoff (4647), and shutdown/restart (1074).
# Uses S4U logon so it can run while the interactive session is ending.
$endTaskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Call It a Day - post end event on lock/logoff/shutdown</Description>
  </RegistrationInfo>
  <Triggers>
    <SessionStateChangeTrigger>
      <Enabled>true</Enabled>
      <StateChange>SessionLock</StateChange>
    </SessionStateChangeTrigger>
    <EventTrigger>
      <Enabled>true</Enabled>
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="Security"&gt;&lt;Select Path="Security"&gt;*[System[EventID=4647]]&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
    </EventTrigger>
    <EventTrigger>
      <Enabled>true</Enabled>
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="System"&gt;&lt;Select Path="System"&gt;*[System[EventID=1074]]&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
    </EventTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$env:USERDOMAIN\$env:USERNAME</UserId>
      <LogonType>S4U</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT1M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions>
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-NoProfile -WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -File "$REPORT_PS1" -Action end</Arguments>
    </Exec>
  </Actions>
</Task>
"@

# Remove old tasks (including legacy CallItaDay-Start name)
foreach ($name in @($TASK_LOGON, $TASK_UNLOCK, $TASK_END, "CallItaDay-Start")) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
}
Register-ScheduledTask -TaskName $TASK_LOGON  -Xml $logonTaskXml  -Force | Out-Null
Register-ScheduledTask -TaskName $TASK_UNLOCK -Xml $unlockTaskXml -Force | Out-Null
Register-ScheduledTask -TaskName $TASK_END    -Xml $endTaskXml    -Force | Out-Null

Write-Host "Tasks registered:"
Write-Host "  $TASK_LOGON  - fires on logon (posts start)"
Write-Host "  $TASK_UNLOCK - fires on screen unlock (posts start)"
Write-Host "  $TASK_END    - fires on lock, logoff, and shutdown (posts end)"
Write-Host ""
Write-Host "Done."
Write-Host "To check task status:"
Write-Host "  Get-ScheduledTask -TaskName $TASK_LOGON  | Get-ScheduledTaskInfo"
Write-Host "  Get-ScheduledTask -TaskName $TASK_UNLOCK | Get-ScheduledTaskInfo"
Write-Host "  Get-ScheduledTask -TaskName $TASK_END    | Get-ScheduledTaskInfo"
