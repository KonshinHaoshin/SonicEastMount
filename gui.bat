@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: 从 .env 文件中读取变量
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "%%A=%%B"
)

:: 构造执行路径
set "PYTHON_PATH=%SOVITS_DIR%\runtime\python.exe"
echo Using python at: %PYTHON_PATH%

:: 运行 gui.py
%PYTHON_PATH% gui.py

pause
