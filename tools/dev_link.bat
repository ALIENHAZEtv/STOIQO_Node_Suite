@echo off
setlocal EnableExtensions EnableDelayedExpansion
title STOIQO Suite - ComfyUI Dev Link Manager
color 0a

pushd "%~dp0.."
set "SUITE_ROOT=%CD%"
popd

set "EXCATHEDRA_COMFY_NODES=%SUITE_ROOT%\..\..\ExCathedra\engines\comfyui\ComfyUI\custom_nodes"
set "LINK_TARGET=%EXCATHEDRA_COMFY_NODES%\STOIQO_Node_Suite"

chcp 65001 >nul

echo ===============================================================================
echo        STOIQO Node Suite — NTFS Junction Link Manager per ExCathedra
echo ===============================================================================
echo.
echo Sorgente Suite: "%SUITE_ROOT%"
echo Target ComfyUI: "%LINK_TARGET%"
echo.

if not exist "%EXCATHEDRA_COMFY_NODES%" (
    echo [ERRORE CRITICO] Directory custom_nodes di ExCathedra non trovata:
    echo "%EXCATHEDRA_COMFY_NODES%"
    echo Verifica che ExCathedra sia presente nel workbench.
    echo.
    pause
    exit /b 1
)

:: Verifica stato attuale
set "IS_JUNCTION=0"
if exist "%LINK_TARGET%" (
    fsutil reparsepoint query "%LINK_TARGET%" >nul 2>&1
    if not errorlevel 1 (
        set "IS_JUNCTION=1"
        echo [STATO ATTUALE] NTFS Junction ATTIVA verso la suite di sviluppo.
    ) else (
        echo [ATTENZIONE] In "%LINK_TARGET%" esiste una cartella fisica reale (NON junction).
    )
) else (
    echo [STATO ATTUALE] Nessun collegamento presente in ComfyUI.
)

echo.
echo Operazioni disponibili:
echo [1] Collega (Crea NTFS Junction per Hot-Reload a zero copie)
echo [2] Scollega (Rimuove la Junction da ComfyUI senza toccare il codice sorgente)
echo [3] Esci
echo.

set /p OPT="Seleziona opzione [1, 2 o 3, default 1]: "
if "%OPT%"=="" set "OPT=1"

if "%OPT%"=="1" (
    if "!IS_JUNCTION!"=="1" (
        echo.
        echo [INFO] La Junction e' gia' configurata ed attiva. Nessuna azione necessaria.
    ) else if exist "%LINK_TARGET%" (
        echo.
        echo [ERRORE] Esiste gia' una cartella in "%LINK_TARGET%". Rimuovila manualmente prima di creare la Junction.
    ) else (
        echo.
        echo Creazione NTFS Junction in corso...
        mklink /J "%LINK_TARGET%" "%SUITE_ROOT%"
        if not errorlevel 1 (
            echo.
            echo [SUCCESSO] Junction creata con successo! Le modifiche al codice si riflettono istantaneamente in ComfyUI.
        ) else (
            echo.
            echo [ERRORE] Impossibile creare la Junction. Assicurati di avere permessi adeguati.
        )
    )
) else if "%OPT%"=="2" (
    if "!IS_JUNCTION!"=="1" (
        echo.
        echo Rimozione Junction da ComfyUI...
        rmdir "%LINK_TARGET%"
        echo [SUCCESSO] Junction rimossa da ComfyUI. I sorgenti in SideProject sono intatti.
    ) else (
        echo.
        echo [INFO] Nessuna Junction da rimuovere.
    )
)

echo.
pause
exit /b 0

