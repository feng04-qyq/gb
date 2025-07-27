@echo off
chcp 65001 >nul
echo 🚀 IBOX管理系统Windows部署脚本
echo ================================

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

REM 检查Docker Compose是否安装
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

echo ✅ Docker环境检查通过

REM 创建必要的目录
echo 📁 创建目录结构...
if not exist "logs\nginx" mkdir logs\nginx
if not exist "ssl" mkdir ssl
if not exist "data" mkdir data

REM 生成SSL证书
echo 🔐 生成SSL证书...
if not exist "ssl\cert.pem" (
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ssl\key.pem -out ssl\cert.pem -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
    echo ✅ SSL证书生成完成
) else (
    echo ✅ SSL证书已存在
)

REM 构建Docker镜像
echo 🐳 构建Docker镜像...
docker-compose build

REM 启动服务
echo 🚀 启动服务...
docker-compose up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 🔍 检查服务状态...
docker-compose ps

REM 测试健康检查
echo 🏥 测试健康检查...
for /l %%i in (1,1,30) do (
    curl -f http://localhost/health >nul 2>&1
    if not errorlevel 1 (
        echo ✅ 服务启动成功！
        goto :success
    )
    echo ⏳ 等待服务启动... (%%i/30)
    timeout /t 2 /nobreak >nul
)

echo ❌ 服务启动超时
goto :end

:success
echo.
echo 🎉 部署完成！
echo ================================
echo 🌐 访问地址:
echo    HTTP:  http://localhost
echo    HTTPS: https://localhost
echo.
echo 📊 管理命令:
echo    查看状态: docker-compose ps
echo    查看日志: docker-compose logs -f
echo    停止服务: docker-compose down
echo    重启服务: docker-compose restart
echo.
echo 🔧 配置文件位置:
echo    应用配置: .\accounts.json
echo    自动登录: .\auto_login_config.json
echo    代理配置: .\proxy_list.json
echo    状态文件: .\status.json
echo.
echo 📝 日志文件位置:
echo    应用日志: .\logs\
echo    Nginx日志: .\logs\nginx\
echo.

REM 运行测试
if exist "test_deployment.py" (
    echo 🧪 运行部署测试...
    python test_deployment.py http://localhost
)

:end
echo.
echo 按任意键退出...
pause >nul 