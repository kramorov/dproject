# build-demo.ps1 -- Docker image build with demo data & push to Cloud.ru
#
# Usage:
#   .\build-demo.ps1                  full build + push
#   .\build-demo.ps1 -BuildOnly       build only, skip push
#   .\build-demo.ps1 -PushOnly        push existing local image (skip build)
#   .\build-demo.ps1 -Clean           remove temp files
#
# Requirements: Docker Desktop running, docker login cr.cloud.ru (once)

param(
    [switch] $BuildOnly,
    [switch] $PushOnly,
    [switch] $Clean
)

# ===== CONFIG =====
$Registry   = "drf-front.cr.cloud.ru"
$TenantId   = "ca62177a-1c49-40f9-9c58-965d01621220"
$ImageName  = "demo-equipment"
$ImageTag   = "v1"
$FullImage  = "$Registry/$TenantId/${ImageName}:$ImageTag"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  build-demo.ps1" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Image : $FullImage"
Write-Host ""

# ===== Clean mode =====
if ($Clean) {
    Write-Host "[CLEAN] Removing temp files..."
    @(".dockerignore.bak", ".dockerignore.demo") | ForEach-Object {
        if (Test-Path $_) { Remove-Item $_ -Force; Write-Host "  removed $_" }
    }
    Write-Host "[OK] Done"
    exit 0
}

# ===== Check Docker =====
docker info >$null 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker is not running. Start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Docker running"

# ===== Push-only mode: skip build, just tag + push =====
if ($PushOnly) {
    Write-Host ""
    Write-Host "[PUSH-ONLY] Checking local image..."
    $exists = docker image inspect "${ImageName}:$ImageTag" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Local image ${ImageName}:$ImageTag not found. Run build first." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Found ${ImageName}:$ImageTag"

    Write-Host ""
    Write-Host "[1/2] Tagging for Cloud.ru..."
    docker tag "${ImageName}:$ImageTag" $FullImage
    Write-Host "[OK] Tag: $FullImage"

    Write-Host ""
    Write-Host "[2/2] Pushing to Cloud.ru..."
    docker push $FullImage
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Push failed. Check docker login $Registry" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  PUSH COMPLETE" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  Image: $FullImage"
    Write-Host "============================================" -ForegroundColor Green
    exit 0
}

# ===== Check DB =====
if (-not (Test-Path "db.sqlite3")) {
    Write-Host "[ERROR] db.sqlite3 not found in project root." -ForegroundColor Red
    Write-Host "        Place your demo database here and re-run."
    exit 1
}
$dbSize = "{0:N1} MB" -f ((Get-Item "db.sqlite3").Length / 1MB)
Write-Host "[OK] db.sqlite3 found ($dbSize)"

# ===== Step 1: prepare .dockerignore (allow sqlite) =====
Write-Host ""
Write-Host "[1/4] Preparing .dockerignore (demo mode -- DB included)..."

if (-not (Test-Path ".dockerignore.bak")) {
    Copy-Item ".dockerignore" ".dockerignore.bak"
}

$ignored = Get-Content ".dockerignore" | Where-Object {
    $_ -notmatch '^\*\.sqlite3' -and $_ -notmatch '^db.*\.sqlite3'
}
$ignored | Set-Content ".dockerignore.demo"
Copy-Item ".dockerignore.demo" ".dockerignore" -Force
Write-Host "[OK] DB included in image"

# ===== Step 2: build =====
Write-Host ""
Write-Host "[2/4] Building Docker image..."

$env:DOCKER_BUILDKIT = "0"
docker build -t "${ImageName}:$ImageTag" .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Build failed" -ForegroundColor Red
    Copy-Item ".dockerignore.bak" ".dockerignore" -Force
    exit 1
}

Copy-Item ".dockerignore.bak" ".dockerignore" -Force
Write-Host "[OK] Image built"

# ===== Step 3: tag =====
Write-Host ""
Write-Host "[3/4] Tagging for Cloud.ru..."
docker tag "${ImageName}:$ImageTag" $FullImage
Write-Host "[OK] Tag: $FullImage"

# ===== Step 4: push =====
if ($BuildOnly) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  Build complete (BuildOnly mode)" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Next steps:"
    Write-Host "    docker push $FullImage"
    Write-Host "    docker run -d -p 8000:8000 ${ImageName}:$ImageTag"
    Write-Host ""
    Write-Host "  Cleanup: .\build-demo.ps1 -Clean"
    Write-Host "============================================" -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "[4/4] Pushing to Cloud.ru Artifact Registry..."
Write-Host "      Login if prompted: docker login $Registry"

docker push $FullImage
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Push failed. Check:" -ForegroundColor Red
    Write-Host "  1. docker login $Registry"
    Write-Host "  2. Artifact Registry created in Cloud.ru console"
    Write-Host "  3. TENANT_ID matches your Cloud.ru tenant"
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  SUCCESS!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Image: $FullImage"
Write-Host ""
Write-Host "  Next: create Container App at"
Write-Host "    https://console.cloud.ru/container-apps"
Write-Host ""
Write-Host "  Settings:"
Write-Host "    Image : $FullImage"
Write-Host "    Port  : 8000"
Write-Host "    vCPU  : 0.2"
Write-Host "    RAM   : 512 MB"
Write-Host "    URL   : your-name.containerapps.ru"
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Local test: docker run -d -p 8000:8000 ${ImageName}:$ImageTag"
Write-Host "  Cleanup   : .\build-demo.ps1 -Clean"
Write-Host "============================================" -ForegroundColor Green
