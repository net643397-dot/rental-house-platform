@echo off
chcp 65001 > nul
echo 房源信息网站启动脚本
echo ========================

echo 第一步: 启动MySQL服务器...
echo 正在后台启动MySQL服务器，请等待...

cd /d "%~dp0"
call conda activate mysql

echo 检查MySQL进程...
tasklist /FI "IMAGENAME eq mysqld.exe" 2>nul | find /I "mysqld.exe" >nul
if not errorlevel 1 (
    echo MySQL服务器已在运行中
) else (
    echo 启动MySQL服务器...
    start /B mysqld --console
    echo 等待MySQL启动完成...
    timeout /t 8 /nobreak > nul
)

echo.
echo 第二步: 检查数据库连接...
mysql -u root -e "USE house; SELECT COUNT(*) as '房源数量' FROM house_info;" 2>nul
if errorlevel 1 (
    echo 警告: 数据库连接失败，请检查MySQL服务状态
    pause
    exit /b 1
)

echo.
echo 第三步: 启动Flask应用...
echo 应用将在 http://127.0.0.1:5000 启动
echo 按 Ctrl+C 可以停止服务
echo.

python app.py

echo.
echo 应用已停止
pause