@echo off
rem chcp quirk (Server 2022 / Win11 cmd builds): `chcp 65001 >nul` with a
rem redirected stdout CONSUMES the whole redirected stdin of the batch —
rem a later `python main.py < in.txt` then sees instant EOF. Feeding chcp
rem its own stdin from nul keeps the script's stdin intact (no-op for
rem interactive console launches).
chcp 65001 >nul <nul
cd /d "%~dp0"
set "_PKG=pipeline"
set "_CACHE=.bundle"
set "_PKGFILE=engine.pkg"
set "_PY=%_CACHE%\python.exe"

if not exist "%_PY%" goto :extract
"%_PY%" -c "pass" >nul 2>&1
if "%ERRORLEVEL%"=="0" goto :launch_bundled
rmdir /s /q "%_CACHE%" 2>nul

:extract
if not exist "%_PKG%\data\%_PKGFILE%" goto :system
rem Keep the window alive during the (silent) extraction: on a cold host
rem unpacking the runtime takes seconds-to-a-minute and a bare black
rem window reads as "hung" to the user.
echo.
echo   Preparing the runtime environment, please wait (first run may take a minute)...
rmdir /s /q "%_CACHE%.tmp" 2>nul
mkdir "%_CACHE%.tmp"
if exist "%SystemRoot%\System32\tar.exe" (
    "%SystemRoot%\System32\tar.exe" -xf "%_PKG%\data\%_PKGFILE%" -C "%_CACHE%.tmp" >nul 2>&1
)
if exist "%_CACHE%.tmp\python.exe" goto :extract_ok
rem Second extractor: PowerShell/.NET ZipFile.
rmdir /s /q "%_CACHE%.tmp" 2>nul
mkdir "%_CACHE%.tmp"
powershell -NoProfile -Command "Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('%_PKG%\data\%_PKGFILE%','%_CACHE%.tmp')" >nul 2>&1
if exist "%_CACHE%.tmp\python.exe" goto :extract_ok
rem Third extractor: Shell.Application via cscript — survives hosts where
rem tar.exe is missing AND PowerShell is policy-blocked ("Access is denied").
rem NOTE 1: goto-style on purpose, NOT inside if() blocks — literal
rem   parentheses in the echoed VBS would close the block early.
rem NOTE 2: Shell.Application only treats *.zip as an archive, so the pkg is
rem   copied to a .zip name first.
rmdir /s /q "%_CACHE%.tmp" 2>nul
mkdir "%_CACHE%.tmp"
copy /y "%_PKG%\data\%_PKGFILE%" "%_CACHE%.tmp\_rt.zip" >nul 2>&1
>"%_CACHE%.tmp\_u.vbs" echo Set sh = CreateObject("Shell.Application")
>>"%_CACHE%.tmp\_u.vbs" echo sh.NameSpace("%CD%\%_CACHE%.tmp").CopyHere sh.NameSpace("%CD%\%_CACHE%.tmp\_rt.zip").Items, 20
cscript //nologo "%_CACHE%.tmp\_u.vbs" >nul 2>&1
del "%_CACHE%.tmp\_u.vbs" >nul 2>&1
del "%_CACHE%.tmp\_rt.zip" >nul 2>&1
if not exist "%_CACHE%.tmp\python.exe" goto :extract_failed

:extract_ok
rem MOTW hygiene: files from a downloaded archive may carry the internet-zone
rem mark; running a marked python.exe yields "Access is denied" on locked-down
rem hosts. Unblock silently (no-op when PowerShell is unavailable).
powershell -NoProfile -Command "Get-ChildItem -Recurse '%_CACHE%.tmp' -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue" >nul 2>&1
"%_CACHE%.tmp\python.exe" -c "pass" >nul 2>&1
if not "%ERRORLEVEL%"=="0" goto :extract_failed
set "_MOVE_TRY=0"
:move_retry
rmdir /s /q "%_CACHE%" 2>nul
move /y "%_CACHE%.tmp" "%_CACHE%" >nul 2>&1
if exist "%_PY%" goto :launch_bundled
set /a "_MOVE_TRY+=1"
if %_MOVE_TRY% lss 4 (
    timeout /t 2 /nobreak >nul
    goto :move_retry
)

:extract_failed
rmdir /s /q "%_CACHE%.tmp" 2>nul

:system
python -V >nul 2>&1
if errorlevel 1 (
    echo.
    echo   Embedded runtime could not be prepared and no system Python was found.
    echo   Re-download this archive or install Python 3.11+ from python.org.
    echo.
    pause
    goto :end
)
python main.py %*
goto :end

:launch_bundled
"%_PY%" main.py %*

:end
