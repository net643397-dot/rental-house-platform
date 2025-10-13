@echo off
setlocal enabledelayedexpansion

REM -------------------------------------------------------------
REM  初始化 house 数据库的辅助脚本
REM -------------------------------------------------------------

where mysql >nul 2>nul
if errorlevel 1 (
    echo [ERROR] 未检测到 ^"mysql^" 命令. 请将 MySQL 安装目录加入 PATH，
    echo        或修改此脚本使用 mysql.exe 的完整路径。
    pause
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"
set "SQL_ADD=%SCRIPT_DIR%add_location_fields.sql"
set "SQL_DATA=%SCRIPT_DIR%house.sql"

if not exist "%SQL_ADD%" (
    echo [ERROR] 未找到 add_location_fields.sql
    pause
    exit /b 1
)

if not exist "%SQL_DATA%" (
    echo [ERROR] 未找到 house.sql
    pause
    exit /b 1
)

echo.
echo ========= 初始化 house 数据库 =========

set /p MYSQL_HOST=MySQL 主机 (默认 127.0.0.1): 
if "%MYSQL_HOST%"=="" set "MYSQL_HOST=127.0.0.1"

set /p MYSQL_PORT=MySQL 端口 (默认 3306): 
if "%MYSQL_PORT%"=="" set "MYSQL_PORT=3306"

set /p MYSQL_USER=MySQL 用户名 (默认 root): 
if "%MYSQL_USER%"=="" set "MYSQL_USER=root"

set /p MYSQL_PASS=MySQL 密码 (留空表示无密码): 

set "MYSQL_ARGS=-h %MYSQL_HOST% -P %MYSQL_PORT% -u %MYSQL_USER%"
if not "%MYSQL_PASS%"=="" set "MYSQL_ARGS=%MYSQL_ARGS% -p%MYSQL_PASS%"

echo.
echo [1/3] 创建 house 数据库...
mysql %MYSQL_ARGS% -e "CREATE DATABASE IF NOT EXISTS house CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
if errorlevel 1 (
    echo [ERROR] 创建数据库失败，请检查上方提示。
    pause
    exit /b 1
)

echo [2/3] 导入 add_location_fields.sql ...
mysql %MYSQL_ARGS% -D house < "%SQL_ADD%"
if errorlevel 1 (
    echo [ERROR] 导入 add_location_fields.sql 失败。
    pause
    exit /b 1
)

echo [3/3] 导入 house.sql (数据较大，请耐心等待) ...
mysql %MYSQL_ARGS% -D house < "%SQL_DATA%"
if errorlevel 1 (
    echo [ERROR] 导入 house.sql 失败。
    pause
    exit /b 1
)

echo.
echo [SUCCESS] house 数据库初始化完成！
echo 现在可以运行 map_house.exe 或 python app.py 了。
pause
endlocal
