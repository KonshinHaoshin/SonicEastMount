@echo off
setlocal EnableDelayedExpansion

:: 检查 .env 是否存在
if not exist ".env" (
    echo ❌ .env 文件不存在，请创建并设置 SOVITS_DIR=目录名（如 GPT-SoVITS-v4-20250422fix）
    pause
    exit /b
)

:: 读取 .env 中的 SOVITS_DIR 变量
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "%%A=%%B"
)

:: 设置 Python 路径
set "PYTHON_PATH=%SOVITS_DIR%\runtime\python.exe"

:: 安装依赖
echo 📦 正在使用 %PYTHON_PATH% 安装依赖...
%PYTHON_PATH% -m pip install -r requirements.txt

pause
