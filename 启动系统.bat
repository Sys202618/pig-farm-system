@echo off
chcp 65001 >nul
title 猪场管理系统
echo ======================================
echo      猪场生产+财务管理系统
echo ======================================
echo.

cd /d "%~dp0"

echo [1/4] 检查Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装
    pause & exit /b 1
)

echo [2/4] 检查依赖...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo     安装依赖中...
    pip install flask flask-cors openpyxl -q
)

echo [3/4] 检查目录...
if not exist "backend" mkdir backend
if not exist "frontend\css" mkdir frontend\css
if not exist "frontend\js" mkdir frontend\js
if not exist "data" mkdir data
if not exist "exports" mkdir exports

echo [4/4] 启动服务...
echo.
echo ================ 启动成功 ================
echo 访问地址: http://127.0.0.1:5000
echo 默认账号: admin  密码: admin123
echo ==========================================
echo 按 Ctrl+C 停止服务
echo.
python backend\app.py
pause
