@echo off
chcp 65001 >nul
color 0A

echo ========================================================
echo 🚀依赖安装
echo ========================================================
echo.

:: 1. 获取路径
set "PLUGIN_DIR=%~dp0"
set "COMFYUI_DIR=%PLUGIN_DIR%..\.."
pushd "%COMFYUI_DIR%"
set "COMFYUI_ROOT=%cd%"
popd

:: 2. 寻找便携版 Python
set "PYTHON_PATH="
if exist "%COMFYUI_ROOT%\..\python_embeded\python.exe" (
    set "PYTHON_PATH=%COMFYUI_ROOT%\..\python_embeded\python.exe"
) else if exist "%COMFYUI_ROOT%\..\python-embeded\python.exe" (
    set "PYTHON_PATH=%COMFYUI_ROOT%\..\python-embeded\python.exe"
) else (
    set "PYTHON_PATH=python"
)

echo [侦测] Python 环境路径: %PYTHON_PATH%
echo [准备] 即将开始安装 (自动跳过已存在的库)...
echo.

:: 3. 尝试使用清华源安装
echo --------------------------------------------------------
echo 正在连接 【清华大学镜像源】 进行高速下载...
echo --------------------------------------------------------
"%PYTHON_PATH%" -m pip install -r "%PLUGIN_DIR%requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple

:: 4. 容灾机制：如果清华源失败，切换阿里源
if %errorlevel% neq 0 (
    echo.
    echo [⚠️ 警告] 清华源连接不稳定或缺少部分库，自动切换至 【阿里云镜像源】...
    echo.
    "%PYTHON_PATH%" -m pip install -r "%PLUGIN_DIR%requirements.txt" -i https://mirrors.aliyun.com/pypi/simple/
)

echo.
echo ========================================================
echo ✅ 安装流程结束！请查看上方是否有红色的报错信息。
echo 如果一切正常，按任意键退出并重启 ComfyUI。
echo ========================================================
pause