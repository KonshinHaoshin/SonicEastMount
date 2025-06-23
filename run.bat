@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

if not exist ".env" (
    echo ❌ .env 文件不存在，请创建并设置 SOVITS_DIR=目录名
    pause
    exit /b
)

:: 读取 .env
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "%%A=%%B"
)

:: 调试输出
echo 📌 SOVITS_DIR = [%SOVITS_DIR%]

set "PYTHON_PATH=%SOVITS_DIR%\runtime\python.exe"
echo 📌 PYTHON_PATH = [%PYTHON_PATH%]

:: 检查路径是否存在
if not exist "%PYTHON_PATH%" (
    echo ❌ Python 路径不存在: %PYTHON_PATH%
    pause
    exit /b
)

:: 安装依赖
echo 📦 正在使用 %PYTHON_PATH% 安装依赖...
"%PYTHON_PATH%" -m pip install -r requirements.txt

pause
