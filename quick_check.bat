@echo off
chcp 65001 > nul
echo 系统状态检查工具
echo ==================

call conda activate mysql

echo 1. 检查conda环境...
conda info --envs | findstr mysql
if errorlevel 1 (
    echo ❌ mysql conda环境不存在
    goto :error
) else (
    echo ✅ mysql conda环境正常
)

echo.
echo 2. 检查MySQL安装...
where mysql >nul 2>&1
if errorlevel 1 (
    echo ❌ MySQL命令不可用
    goto :error
) else (
    echo ✅ MySQL已安装
)

echo.
echo 3. 检查MySQL服务状态...
tasklist /FI "IMAGENAME eq mysqld.exe" 2>nul | find /I "mysqld.exe" >nul
if errorlevel 1 (
    echo ❌ MySQL服务未运行
    echo 请运行: mysqld --console
) else (
    echo ✅ MySQL服务正在运行
)

echo.
echo 4. 检查数据库连接...
mysql -u root -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo ❌ 无法连接MySQL数据库
    goto :error
) else (
    echo ✅ 数据库连接正常
)

echo.
echo 5. 检查house数据库...
mysql -u root -e "USE house;" >nul 2>&1
if errorlevel 1 (
    echo ❌ house数据库不存在
    echo 请运行: mysql -u root -e "CREATE DATABASE house;"
    goto :error
) else (
    echo ✅ house数据库存在
)

echo.
echo 6. 检查房源数据...
for /f "skip=1" %%i in ('mysql -u root -D house -e "SELECT COUNT(*) FROM house_info;" 2^>nul') do set count=%%i
if "%count%"=="0" (
    echo ❌ 房源数据为空
    echo 请运行: mysql -u root -D house ^< house.sql
) else (
    echo ✅ 房源数据: %count% 条记录
)

echo.
echo 7. 检查数据表结构...
mysql -u root -D house -e "DESCRIBE house_info;" | findstr latitude >nul 2>&1
if errorlevel 1 (
    echo ❌ 缺少经纬度字段
    echo 请运行: mysql -u root -D house ^< add_location_fields.sql
) else (
    echo ✅ 数据表结构完整
)

echo.
echo 8. 检查端口占用...
netstat -an | findstr :5000 >nul 2>&1
if not errorlevel 1 (
    echo ⚠️  端口5000已被占用
) else (
    echo ✅ 端口5000可用
)

echo.
echo ==================
echo 系统检查完成！
echo.
pause
exit /b 0

:error
echo.
echo ==================
echo 发现问题，请参考《启动操作指南.md》
pause
exit /b 1