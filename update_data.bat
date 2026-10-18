@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
setlocal
cd /d "%~dp0"

set "GIT=%~dp0.tools\PortableGit\bin\git.exe"
set "PY=%~dp0.venv\Scripts\python.exe"

echo ============================================
echo   P3 Data Auto Update
echo   %date% %time%
echo ============================================
echo.

if not exist "%GIT%" (
    echo [ERROR] PortableGit not found:
    echo         %GIT%
    goto :fail
)
if not exist "%PY%" (
    echo [ERROR] Python not found:
    echo         %PY%
    goto :fail
)

echo [1/4] Fetching latest lottery data...
"%PY%" fetch_p3_data.py
if errorlevel 1 (
    echo.
    echo [FAILED] Fetch error, aborted.
    goto :fail
)
echo.

echo [2/4] Checking for changes...
"%GIT%" add data/p3.csv
"%GIT%" diff --cached --quiet
if not errorlevel 1 (
    echo [SKIP] No changes, nothing to commit.
    goto :done
)

echo [3/4] Committing...
"%GIT%" -c credential.helper= commit -m "data: update p3 data %date%"
if errorlevel 1 (
    echo.
    echo [FAILED] Commit failed.
    goto :fail
)
echo.

echo [4/4] Pushing to GitHub...
"%GIT%" -c credential.helper= -c http.sslVerify=false push origin main
if errorlevel 1 (
    echo.
    echo [FAILED] Push failed. Check network or GitHub token.
    goto :fail
)

:done
echo.
echo ============================================
echo   DONE
echo ============================================
echo.
pause
goto :eof

:fail
echo.
echo ============================================
echo   ABORTED - see messages above
echo ============================================
echo.
pause
exit /b 1