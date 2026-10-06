Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$server = "pingaan@pingaan.tplinkdns.com"
$localAddress = "127.0.0.1"
$localPort = 5433

$keyPath = Join-Path `
    $env:USERPROFILE `
    ".ssh\sites_server1_ed25519"

$configDirectory = Join-Path `
    $env:LOCALAPPDATA `
    "Sites"

$logPath = Join-Path `
    $configDirectory `
    "ssh-tunnel.log"


function Test-SitesPort {
    $client = [System.Net.Sockets.TcpClient]::new()

    try {
        $client.Connect(
            $localAddress,
            $localPort
        )

        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}


if (Test-SitesPort) {
    Write-Host (
        "Sites database tunnel is already connected " +
        "on ${localAddress}:${localPort}."
    )

    exit 0
}


if (-not (Test-Path -LiteralPath $keyPath)) {
    throw "SSH key does not exist: $keyPath"
}


New-Item `
    -ItemType Directory `
    -Force `
    $configDirectory |
Out-Null

Remove-Item `
    -LiteralPath $logPath `
    -Force `
    -ErrorAction SilentlyContinue


$sshExecutable = (
    Get-Command ssh.exe -ErrorAction Stop
).Source

$sshArguments = (
    '-N -T ' +
    '-i "{0}" ' +
    '-L {1}:{2}:127.0.0.1:5433 ' +
    '-o BatchMode=yes ' +
    '-o ExitOnForwardFailure=yes ' +
    '-o ServerAliveInterval=30 ' +
    '-o ServerAliveCountMax=3 ' +
    '{3}'
) -f (
    $keyPath,
    $localAddress,
    $localPort,
    $server
)


Write-Host "Starting the Sites database tunnel..."

$sshProcess = Start-Process `
    -FilePath $sshExecutable `
    -ArgumentList $sshArguments `
    -WindowStyle Hidden `
    -RedirectStandardError $logPath `
    -PassThru


$deadline = (Get-Date).AddSeconds(15)

while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500

    if (Test-SitesPort) {
        Write-Host (
            "Sites database tunnel connected on " +
            "${localAddress}:${localPort}."
        )

        exit 0
    }

    if ($sshProcess.HasExited) {
        $details = ""

        if (Test-Path -LiteralPath $logPath) {
            $details = Get-Content `
                -LiteralPath $logPath `
                -Raw
        }

        throw (
            "The SSH process stopped unexpectedly.`n" +
            $details
        )
    }
}


if (-not $sshProcess.HasExited) {
    Stop-Process `
        -Id $sshProcess.Id `
        -Force
}

throw (
    "The SSH tunnel did not connect within 15 seconds. " +
    "See $logPath"
)