@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

REM ============================================================
REM  排列三数据自动更新 + 推送到 GitHub
REM  用法：双击运行即可
REM ============================================================

set "GIT=%~dp0.tools\PortableGit\bin\git.exe"
set "PY=%~dp0.venv\Scripts\python.exe"

echo ============================================
echo   排列三数据自动更新
echo   %date% %time%
echo ============================================
echo.

REM ---------- 0. 环境检查 ----------
if not exist "%GIT%" (
    echo [错误] 找不到便携版 Git：
    echo        %GIT%
    echo        请确认 .tools\PortableGit 目录存在。
    goto :fail
)
if not exist "%PY%" (
    echo [错误] 找不到 Python：
    echo        %PY%
    echo        请确认 .venv 虚拟环境存在。
    goto :fail
)

REM ---------- 1. 抓取数据 ----------
echo [1/4] 正在抓取最新开奖数据...
"%PY%" fetch_p3_data.py
if errorlevel 1 (
    echo.
    echo [失败] 数据抓取出错，本次更新中止。
    goto :fail
)
echo.

REM ---------- 2. 检查是否有变化 ----------
echo [2/4] 检查数据是否有更新...
"%GIT%" add data/p3.csv
"%GIT%" diff --cached --quiet
if not errorlevel 1 (
    echo [跳过] 数据没有变化，无需提交。
    goto :done
)

REM ---------- 3. 提交 ----------
echo [3/4] 提交变更...
"%GIT%" commit -m "data: 更新排列三数据 %date%"
if errorlevel 1 (
    echo.
    echo [失败] 提交失败。
    goto :fail
)
echo.

REM ---------- 4. 推送 ----------
echo [4/4] 推送到 GitHub...
"%GIT%" push origin main
if errorlevel 1 (
    echo.
    echo [失败] 推送失败。
    echo        常见原因：网络不通、GitHub Token 失效或无权限。
    goto :fail
)

:done
echo.
echo ============================================
echo   全部完成 ✅
echo ============================================
echo.
pause
goto :eof

:fail
echo.
echo ============================================
echo   执行中断 ❌   请查看上面的错误信息
echo ============================================
echo.
pause
exit /b 1
