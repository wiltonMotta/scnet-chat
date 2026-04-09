@echo off
REM SCNet Chat 跨平台启动脚本 (Windows)
REM 自动检测并使用正确的 Python 解释器

setlocal enabledelayedexpansion

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "SCNET_PY=%SCRIPT_DIR%scnet.py"

REM 检查 python 是否存在
where python >nul 2>&1
if %errorlevel% == 0 (
    python "%SCNET_PY%" %*
    exit /b %errorlevel%
)

REM 检查 python3 是否存在
where python3 >nul 2>&1
if %errorlevel% == 0 (
    python3 "%SCNET_PY%" %*
    exit /b %errorlevel%
)

echo 错误: 未找到 Python 解释器，请安装 Python 3 并确保 python 或 python3 命令可用 >&2
exit /b 1
