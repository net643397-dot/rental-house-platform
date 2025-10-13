@echo off
chcp 65001 > nul
echo 百度地图API地理编码处理工具
echo ================================

cd /d "%~dp0"
call conda activate mysql

echo 📊 数据统计分析
echo ----------------

echo 检查数据库连接...
mysql -u root -D house -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo ❌ 数据库连接失败
    echo 请确保MySQL服务正在运行
    pause
    exit /b 1
)

echo 获取处理进度信息...
for /f "skip=1" %%i in ('mysql -u root -D house -e "SELECT COUNT(*) FROM house_info WHERE latitude IS NULL OR longitude IS NULL;" 2^>nul') do set remaining=%%i

for /f "skip=1" %%i in ('mysql -u root -D house -e "SELECT COUNT(*) FROM house_info WHERE latitude IS NOT NULL AND longitude IS NOT NULL;" 2^>nul') do set completed=%%i

for /f "skip=1" %%i in ('mysql -u root -D house -e "SELECT COUNT(*) FROM house_info;" 2^>nul') do set total=%%i

echo.
echo 📈 当前进度:
echo    总记录数: %total%
echo    已完成: %completed%
echo    待处理: %remaining%
if %remaining% GTR 0 (
    set /a progress=completed*100/total
    echo    完成率: !progress!%%
) else (
    echo    完成率: 100%%
)

echo.
echo 💰 配额规划:
echo    百度API免费配额: 100,000次/天
echo    建议处理量: 90,000次/天
if %remaining% LEQ 90000 (
    echo    预计完成时间: 1天
) else (
    set /a days=remaining/90000+1
    echo    预计完成时间: !days!天
)

echo.
echo ⚡ 处理速度:
echo    处理频率: 5次/秒
echo    预计用时: 约5小时处理90,000条

echo.
echo 📝 注意事项:
echo    1. 确保网络连接稳定
echo    2. 处理过程中会自动保存进度
echo    3. 可随时按Ctrl+C停止
echo    4. 支持断点续传

echo.
if %remaining% EQU 0 (
    echo 🎉 所有记录已处理完成！
    pause
    exit /b 0
)

echo 准备开始处理 %remaining% 条记录...
set /p confirm=确认开始处理？(Y/N):

if /i "%confirm%" NEQ "Y" (
    echo 已取消处理
    pause
    exit /b 0
)

echo.
echo 🚀 启动地理编码处理...
echo ================================

python daily_geocoding.py

echo.
echo 处理完成，检查最终状态...
for /f "skip=1" %%i in ('mysql -u root -D house -e "SELECT COUNT(*) FROM house_info WHERE latitude IS NULL OR longitude IS NULL;" 2^>nul') do set final_remaining=%%i

echo 最终剩余待处理: %final_remaining% 条

if %final_remaining% EQU 0 (
    echo 🎉 恭喜！所有地理编码处理完成！
) else (
    echo ℹ️  还有 %final_remaining% 条记录待处理
    echo 明天可继续处理剩余记录
)

pause