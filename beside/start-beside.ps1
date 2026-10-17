param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$besideRoot = $PSScriptRoot
$besideUrl = 'http://127.0.0.1:3212/'
$besidePython = Join-Path ([Environment]::GetFolderPath('UserProfile')) '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe'
$besideScript = Join-Path $besideRoot 'collector.py'
$besideData = Join-Path $besideRoot 'data'
$besideListener = Get-NetTCPConnection -LocalPort 3212 -State Listen -ErrorAction SilentlyContinue
if ($besideListener) {
    $besideStatus = Invoke-RestMethod ($besideUrl + 'presence') -TimeoutSec 3
    $besideOwner = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $besideListener[0].OwningProcess)
    if ($besideStatus.schema -ne 'beside.presence.v1' -or -not $besideOwner.CommandLine.Contains($besideScript)) {
        throw 'Port 3212 belongs to another service. Nothing was changed.'
    }
} else {
    if (-not (Test-Path -LiteralPath $besidePython)) { throw 'Bundled Python runtime was not found.' }
    New-Item -ItemType Directory -Path $besideData -Force | Out-Null
    $besideProcess = Start-Process -FilePath $besidePython -ArgumentList ('"' + $besideScript + '"') -WorkingDirectory $besideRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $besideData 'stdout.log') -RedirectStandardError (Join-Path $besideData 'stderr.log') -PassThru
    $besideReady = $false
    for ($besideAttempt = 0; $besideAttempt -lt 20; $besideAttempt++) {
        Start-Sleep -Milliseconds 250
        if ($besideProcess.HasExited) { throw 'Collector exited. See data/stderr.log.' }
        try {
            $besideStatus = Invoke-RestMethod ($besideUrl + 'presence') -TimeoutSec 1
            if ($besideStatus.schema -eq 'beside.presence.v1') { $besideReady = $true; break }
        } catch { }
    }
    if (-not $besideReady) { throw 'Collector did not become ready. See data/stderr.log.' }
}
if (-not $NoBrowser) { Start-Process -FilePath $besideUrl -WindowStyle Hidden }
Write-Output ('Beside: ' + $besideStatus.state + ' | ' + $besideUrl)
