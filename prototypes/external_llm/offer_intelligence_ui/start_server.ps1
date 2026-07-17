Write-Host ""
Write-Host " Offer Intelligence - AI Content Factory" -ForegroundColor Cyan
Write-Host " Prototipo visual isolado - FASE 2" -ForegroundColor Cyan
Write-Host ""

$port = 8765
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if port is in use
$inUse = netstat -an | Select-String ":$port "
if ($inUse) {
    Write-Warning "Porta $port ja esta em uso. Tentando porta $($port+1)..."
    $port++
}

Write-Host " Servidor local: http://localhost:$port" -ForegroundColor Green
Write-Host " Pressione CTRL+C para parar" -ForegroundColor Gray
Write-Host ""

Set-Location $dir
python -m http.server $port

if (-not $?) {
    Write-Host ""
    Write-Host " [ERRO] Falha ao iniciar servidor." -ForegroundColor Red
    Write-Host " Execute manualmente no terminal:" -ForegroundColor Yellow
    Write-Host "   cd $dir" -ForegroundColor Yellow
    Write-Host "   python -m http.server $port" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Pressione Enter para sair"
}
