@echo off
chcp 65001 > nul
title EMC Soldas - Conectividade Remota Cloudflare Tunnel

echo ===============================================================================
echo                EMC SOLDAS - INICIALIZADOR DE TUNEL CLOUDFLARE
echo ===============================================================================
echo.

set CLOUDFLARED_BIN=%~dp0cloudflared.exe

if not exist "%CLOUDFLARED_BIN%" (
    set CLOUDFLARED_BIN=%~dp0..\cloudflared.exe
)

if not exist "%CLOUDFLARED_BIN%" (
    echo [ERRO] O executavel cloudflared.exe nao foi encontrado na pasta tools!
    echo.
    pause
    exit /b 1
)

echo [OK] cloudflared localizado com sucesso!
echo.
echo [INICIANDO] Conectando tunel seguro para o servidor local: http://localhost:8000
echo.
echo -------------------------------------------------------------------------------
echo INSTRUCOES:
echo 1. O servidor Django precisa estar rodando (python manage.py runserver 8000).
echo 2. Aguarde alguns instantes ate aparecer a linha com "https://...trycloudflare.com".
echo 3. Copie essa URL e acesse no seu celular ou notebook fora de casa.
echo 4. Para encerrar o tunel ao terminar, feche esta janela ou pressione Ctrl+C.
echo -------------------------------------------------------------------------------
echo.

"%CLOUDFLARED_BIN%" tunnel --url http://localhost:8000

echo.
echo Tunel finalizado.
pause
