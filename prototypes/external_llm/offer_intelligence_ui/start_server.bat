@echo off
chcp 65001 >nul
set PORT=8765
set DIR=%~dp0

:check_port
netstat -an | findstr ":%PORT% " >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo.
    echo  [AVISO] Porta %PORT% ja esta em uso.
    echo  Talvez o servidor ja esteja rodando.
    echo  Tente abrir http://localhost:%PORT%
    echo.
    choice /C SN /M "Tentar outra porta (S) ou sair (N)"
    if errorlevel 2 exit /b
    set /a PORT=%PORT%+1
    goto check_port
)

echo.
echo  ========================================
echo    Offer Intelligence - AI Content Factory
echo    Prototipo visual isolado - FASE 2
echo  ========================================
echo.
echo  Servidor local: http://localhost:%PORT%
echo  Pressione CTRL+C para parar
echo.

cd /d "%DIR%"
python -m http.server %PORT%
if %ERRORLEVEL% neq 0 (
    echo.
    echo  [ERRO] Falha ao iniciar servidor.
    echo  Certifique-se de que Python 3 esta instalado.
    echo  Ou execute manualmente: python -m http.server %PORT%
    echo.
    pause
)
