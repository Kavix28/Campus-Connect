<#
.SYNOPSIS
    Enterprise Docker Auto-Heal Script for Oudience Chatbot

.DESCRIPTION
    Autonomous self-healing deployment system with 3 phases:
      Phase 1 — Image validation, tag update, digest verification
      Phase 2 — Dependency validation, auto-rebuild if broken
      Phase 3 — Health verification, restart-loop detection, final status

.PARAMETER TargetTag
    Target image tag to deploy. Default: v1.2

.PARAMETER MaxRetries
    Max retry attempts for network operations. Default: 3

.PARAMETER SkipWSLRestart
    Skip WSL restart even if Docker engine is unresponsive.

.PARAMETER ComposeFile
    Override compose file path. Default: auto-detect.

.EXAMPLE
    .\docker-auto-heal.ps1
    .\docker-auto-heal.ps1 -TargetTag v1.3 -MaxRetries 5
#>

param(
    [string]$TargetTag = "v1.2",
    [int]$MaxRetries = 3,
    [switch]$SkipWSLRestart,
    [string]$ComposeFile = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# =====================================================================
# CONFIGURATION
# =====================================================================
$script:ImageName = "kavix28/oudience-chatbot"
$script:ContainerName = "oudience_chatbot_prod"
$script:HealthUrl = "http://localhost:5001/test/system/health"
$script:ExitCode = 0

# =====================================================================
# LOGGING HELPERS
# =====================================================================
function Write-Phase { param([string]$M) Write-Host "`n$('='*60)" -Fg Cyan; Write-Host "  $M" -Fg Cyan; Write-Host "$('='*60)" -Fg Cyan }
function Write-Step { param([string]$M) Write-Host "  --> $M" -Fg White }
function Write-Ok { param([string]$M) Write-Host "  [OK]   $M" -Fg Green }
function Write-Fail { param([string]$M) Write-Host "  [FAIL] $M" -Fg Red; $script:ExitCode = 1 }
function Write-Warn { param([string]$M) Write-Host "  [WARN] $M" -Fg Yellow }
function Write-Detail { param([string]$M) Write-Host "         $M" -Fg DarkGray }

# =====================================================================
# RETRY HELPER
# =====================================================================
function Invoke-WithRetry {
    param([ScriptBlock]$Action, [string]$Label, [int]$Retries = $MaxRetries)
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            & $Action
            return $true
        }
        catch {
            Write-Warn "$Label — attempt $i/$Retries failed: $_"
            if ($i -lt $Retries) { Start-Sleep -Seconds (5 * $i) }
        }
    }
    Write-Fail "$Label — all $Retries attempts failed"
    return $false
}

# =====================================================================
# PRE-FLIGHT: Docker Engine & WSL
# =====================================================================
function Assert-DockerReady {
    Write-Step "Checking Docker engine..."
    try {
        $null = docker info 2>&1
        Write-Ok "Docker engine is responsive"
        return
    }
    catch {
        Write-Warn "Docker engine not responding"
    }

    if ($SkipWSLRestart) {
        throw "Docker engine unresponsive and -SkipWSLRestart is set"
    }

    Write-Step "Restarting WSL..."
    wsl --shutdown 2>$null
    Start-Sleep -Seconds 8

    try {
        $null = docker info 2>&1
        Write-Ok "Docker engine recovered after WSL restart"
    }
    catch {
        throw "Docker engine still unresponsive after WSL restart"
    }
}

function Assert-DockerCompose {
    Write-Step "Checking Docker Compose..."
    $ver = docker compose version --short 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose not available" }
    Write-Ok "Docker Compose $ver"
}

# =====================================================================
# DETECT COMPOSE FILE
# =====================================================================
function Find-ComposeFile {
    Write-Step "Detecting compose file..."

    if ($ComposeFile -and (Test-Path $ComposeFile)) {
        Write-Ok "Using override: $ComposeFile"
        return $ComposeFile
    }

    $candidates = @("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")
    $found = $candidates | Where-Object { Test-Path $_ }

    if (-not $found) { throw "No docker-compose file found in $(Get-Location)" }

    if ($found.Count -gt 1) {
        Write-Warn "Multiple compose files: $($found -join ', ')"
    }

    $chosen = if ($found -is [array]) { $found[0] } else { $found }
    Write-Ok "Using: $chosen"
    return $chosen
}

# =====================================================================
# PHASE 1 — AUTO IMAGE VALIDATION
# =====================================================================
function Invoke-Phase1 {
    param([string]$File)
    Write-Phase "PHASE 1 — IMAGE VALIDATION"

    # 1a. Read current tag
    Write-Step "Reading current image tag..."
    $content = Get-Content $File -Raw
    if ($content -notmatch "image:\s*${script:ImageName}:([\w\.\-]+)") {
        throw "Cannot parse image tag from $File"
    }
    $currentTag = $Matches[1]
    Write-Detail "Current tag: $currentTag"

    # 1b. Update if needed
    if ($currentTag -ne $TargetTag) {
        Write-Warn "Tag mismatch: $currentTag != $TargetTag"
        $backup = "$File.bak.$(Get-Date -f yyyyMMdd_HHmmss)"
        Copy-Item $File $backup
        Write-Detail "Backup: $backup"

        $content = $content -replace "(image:\s*${script:ImageName}:)[\w\.\-]+", "`${1}$TargetTag"
        [System.IO.File]::WriteAllText((Resolve-Path $File).Path, $content)
        Write-Ok "Tag updated to $TargetTag"
    }
    else {
        Write-Ok "Tag already $TargetTag"
    }

    # 1c. Validate compose config
    Write-Step "Validating compose config..."
    $resolved = docker compose -f $File config 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Compose config invalid: $resolved"
        throw "Invalid compose configuration"
    }
    if ($resolved -match "${script:ImageName}:${TargetTag}") {
        Write-Ok "Config resolves correct image"
    }
    else {
        Write-Warn "Config output does not contain expected image"
    }

    # 1d. Full reset
    Write-Step "Full reset (down --volumes --rmi all)..."
    docker compose -f $File down --volumes --rmi all 2>&1 | Out-Null
    Write-Ok "Environment cleaned"

    # 1e. Pull image
    Write-Step "Pulling image..."
    $pulled = Invoke-WithRetry -Label "docker compose pull" -Action {
        docker compose -f $File pull 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "pull failed" }
    }
    if (-not $pulled) { throw "Image pull failed after retries" }
    Write-Ok "Image pulled"

    # 1f. Verify digest
    Write-Step "Verifying image digest..."
    try {
        $inspectRaw = docker image inspect "${script:ImageName}:${TargetTag}" --format "{{json .RepoDigests}}" 2>&1
        if ($inspectRaw -and $inspectRaw -ne "null" -and $inspectRaw -ne "[]") {
            $digest = ($inspectRaw | ConvertFrom-Json)[0]
            Write-Ok "Local digest: $digest"
        }
        else {
            Write-Warn "No digest available (local-only image)"
        }
    }
    catch {
        Write-Warn "Digest check skipped: $_"
    }
}

# =====================================================================
# PHASE 2 — DEPENDENCY VALIDATION
# =====================================================================
function Invoke-Phase2 {
    param([string]$File)
    Write-Phase "PHASE 2 — DEPENDENCY VALIDATION"

    # 2a. Start container
    Write-Step "Starting container..."
    docker compose -f $File up -d 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Container failed to start" }
    Write-Ok "Container started"

    Write-Step "Waiting 15s for stabilization..."
    Start-Sleep -Seconds 15

    # 2b. Check container is actually running
    $state = docker inspect $script:ContainerName --format "{{.State.Status}}" 2>&1
    if ($state -ne "running") {
        Write-Fail "Container state: $state (expected: running)"
        Write-Step "Last 30 container logs:"
        docker logs --tail 30 $script:ContainerName 2>&1 | ForEach-Object { Write-Detail $_ }
        throw "Container not in running state"
    }
    Write-Ok "Container state: running"

    # 2c. Verify prometheus_client
    Write-Step "Testing: python -c 'import prometheus_client'..."
    $importResult = docker exec $script:ContainerName python -c "import prometheus_client; print('OK')" 2>&1
    if ($importResult -match "OK") {
        Write-Ok "prometheus_client verified"
        return
    }

    # 2d. Module missing — rebuild flow
    Write-Fail "prometheus_client missing — initiating rebuild"

    docker compose -f $File down 2>&1 | Out-Null

    # Check requirements.txt
    Write-Step "Checking requirements.txt..."
    if (Test-Path "requirements.txt") {
        $req = Get-Content "requirements.txt" -Raw
        if ($req -notmatch "prometheus.client") {
            Add-Content "requirements.txt" "prometheus-client"
            Write-Ok "Added prometheus-client to requirements.txt"
        }
        else {
            Write-Ok "prometheus-client already in requirements.txt"
        }
    }

    # Determine next version
    $nextTag = Invoke-SemanticBump $TargetTag
    Write-Step "Rebuilding as ${script:ImageName}:$nextTag..."

    # Build
    docker build --no-cache -t "${script:ImageName}:${nextTag}" . 2>&1 | ForEach-Object { Write-Detail $_ }
    if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }
    Write-Ok "Image built: $nextTag"

    # Push with retry
    Write-Step "Pushing ${script:ImageName}:${nextTag}..."
    $pushed = Invoke-WithRetry -Label "docker push" -Action {
        docker push "${script:ImageName}:${nextTag}" 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "push failed" }
    }
    if (-not $pushed) { Write-Warn "Push failed — continuing with local image" }
    else { Write-Ok "Image pushed" }

    # Update compose file
    $content = Get-Content $File -Raw
    $content = $content -replace "(image:\s*${script:ImageName}:)[\w\.\-]+", "`${1}$nextTag"
    [System.IO.File]::WriteAllText((Resolve-Path $File).Path, $content)
    Write-Ok "Compose updated to $nextTag"

    # Restart
    docker compose -f $File up -d 2>&1 | Out-Null
    Start-Sleep -Seconds 15

    # Re-verify
    $importResult = docker exec $script:ContainerName python -c "import prometheus_client; print('OK')" 2>&1
    if ($importResult -match "OK") {
        Write-Ok "prometheus_client verified after rebuild"
    }
    else {
        Write-Fail "prometheus_client STILL missing after rebuild"
        throw "Dependency fix failed"
    }
}

function Invoke-SemanticBump {
    param([string]$Tag)
    if ($Tag -match "^v?(\d+)\.(\d+)$") {
        return "v$($Matches[1]).$([int]$Matches[2] + 1)"
    }
    elseif ($Tag -match "^v?(\d+)\.(\d+)\.(\d+)$") {
        return "v$($Matches[1]).$($Matches[2]).$([int]$Matches[3] + 1)"
    }
    return "${Tag}-fix"
}

# =====================================================================
# PHASE 3 — HEALTH VERIFICATION
# =====================================================================
function Invoke-Phase3 {
    Write-Phase "PHASE 3 — HEALTH VERIFICATION"

    # 3a. Wait for health endpoint
    Write-Step "Waiting 25s for application startup (model loading)..."
    Start-Sleep -Seconds 25

    # 3b. Health check with retry
    Write-Step "Testing $script:HealthUrl..."
    $healthOk = $false
    for ($i = 1; $i -le 3; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri $script:HealthUrl -TimeoutSec 15 -UseBasicParsing
            if ($resp.StatusCode -eq 200) {
                Write-Ok "Health check PASSED (HTTP $($resp.StatusCode))"
                Write-Detail $resp.Content
                $healthOk = $true
                break
            }
        }
        catch {
            Write-Warn "Health attempt $i/3: $_"
            Start-Sleep -Seconds 10
        }
    }
    if (-not $healthOk) { Write-Fail "Health endpoint unreachable" }

    # 3c. Restart-loop detection
    Write-Step "Checking for restart loops..."
    $restartCount = docker inspect $script:ContainerName --format "{{.RestartCount}}" 2>&1
    if ($restartCount -and [int]$restartCount -gt 0) {
        Write-Warn "Container has restarted $restartCount time(s)"
    }
    else {
        Write-Ok "No restart loops detected"
    }

    # 3d. Port binding
    Write-Step "Verifying port binding..."
    $ports = docker port $script:ContainerName 2>&1
    if ($ports -match "5001") {
        Write-Ok "Port 5001 bound correctly"
        Write-Detail $ports
    }
    else {
        Write-Fail "Port 5001 not bound"
    }

    # 3e. Final status table
    Write-FinalStatus -HealthOk $healthOk
}

# =====================================================================
# FINAL STATUS TABLE
# =====================================================================
function Write-FinalStatus {
    param([bool]$HealthOk)
    Write-Phase "FINAL STATUS REPORT"

    try {
        $info = docker inspect $script:ContainerName --format json 2>&1 | ConvertFrom-Json

        $image = $info.Config.Image
        $state = $info.State.Status
        $health = if ($info.State.Health) { $info.State.Health.Status } else { "n/a" }
        $started = $info.State.StartedAt
        $restart = $info.RestartCount

        # Dependency check
        $depResult = docker exec $script:ContainerName python -c "import prometheus_client; print('PASS')" 2>&1
        $depOk = $depResult -match "PASS"

        # Digest
        try {
            $dgRaw = docker image inspect $image --format "{{json .RepoDigests}}" 2>&1
            $digest = if ($dgRaw -and $dgRaw -ne "null" -and $dgRaw -ne "[]") {
                $d = ($dgRaw | ConvertFrom-Json)[0]
                if ($d.Length -gt 50) { $d.Substring(0, 47) + "..." } else { $d }
            }
            else { "local-only" }
        }
        catch { $digest = "unknown" }

        # Table
        Write-Host ""
        Write-Host "  ┌──────────────────────┬────────────────────────────────────────────────┐" -Fg Cyan
        Write-Host "  │ Property             │ Value                                          │" -Fg Cyan
        Write-Host "  ├──────────────────────┼────────────────────────────────────────────────┤" -Fg Cyan

        $rows = @(
            @("Running Image", $image),
            @("Container Status", $state),
            @("Health Status", $health),
            @("Restart Count", "$restart"),
            @("Started At", $started),
            @("Dependency Check", $(if ($depOk) { "PASS" }else { "FAIL" })),
            @("Digest", $digest)
        )
        foreach ($r in $rows) {
            $label = $r[0].PadRight(20)
            $value = $r[1]
            if ($value.Length -gt 46) { $value = $value.Substring(0, 43) + "..." }
            $value = $value.PadRight(46)
            $color = if ($r[1] -match "running|healthy|PASS") { "Green" }
            elseif ($r[1] -match "unhealthy|FAIL|restarting") { "Red" }
            else { "White" }
            Write-Host "  │ " -Fg Cyan -NoNewline
            Write-Host $label -Fg White -NoNewline
            Write-Host " │ " -Fg Cyan -NoNewline
            Write-Host $value -Fg $color -NoNewline
            Write-Host " │" -Fg Cyan
        }
        Write-Host "  └──────────────────────┴────────────────────────────────────────────────┘" -Fg Cyan

        # Verdict
        if ($state -eq "running" -and $depOk -and $HealthOk) {
            Write-Host "`n  ✅ DEPLOYMENT SUCCESSFUL" -Fg Green
        }
        else {
            Write-Host "`n  ⚠️  DEPLOYMENT COMPLETED WITH ISSUES" -Fg Yellow
            $script:ExitCode = 1
        }
    }
    catch {
        Write-Fail "Could not generate status table: $_"
    }
}

# =====================================================================
# MAIN
# =====================================================================
function Main {
    Write-Host ""
    Write-Host "  ╔═══════════════════════════════════════════════════╗" -Fg Cyan
    Write-Host "  ║   Oudience Chatbot — Enterprise Auto-Heal        ║" -Fg Cyan
    Write-Host "  ║   Target: ${script:ImageName}:${TargetTag}       " -Fg Cyan
    Write-Host "  ╚═══════════════════════════════════════════════════╝" -Fg Cyan

    $timer = [System.Diagnostics.Stopwatch]::StartNew()

    try {
        Assert-DockerReady
        Assert-DockerCompose
        $file = Find-ComposeFile
        Invoke-Phase1 -File $file
        Invoke-Phase2 -File $file
        Invoke-Phase3
    }
    catch {
        Write-Fail "FATAL: $_"
        Write-Host $_.ScriptStackTrace -Fg DarkRed
    }

    $timer.Stop()
    Write-Host "`n  ⏱  Elapsed: $([math]::Round($timer.Elapsed.TotalSeconds, 1))s" -Fg DarkGray
    exit $script:ExitCode
}

Main
