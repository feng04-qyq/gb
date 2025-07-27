#!/bin/bash

# IBOX管理系统快速部署脚本
# 适用于本地测试和快速部署

set -e

echo "🚀 IBOX管理系统快速部署"
echo "================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建目录结构..."
mkdir -p logs/nginx
mkdir -p ssl
mkdir -p data

# 生成SSL证书
echo "🔐 生成SSL证书..."
if [ ! -f ssl/cert.pem ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem -out ssl/cert.pem \
        -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
    echo "✅ SSL证书生成完成"
else
    echo "✅ SSL证书已存在"
fi

# 设置文件权限
echo "🔧 设置文件权限..."
chmod +x start.sh
chmod 644 *.json 2>/dev/null || true

# 构建Docker镜像
echo "🐳 构建Docker镜像..."
docker-compose build

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 测试健康检查
echo "🏥 测试健康检查..."
for i in {1..30}; do
    if curl -f http://localhost/health >/dev/null 2>&1; then
        echo "✅ 服务启动成功！"
        break
    fi
    echo "⏳ 等待服务启动... ($i/30)"
    sleep 2
done

# 显示访问信息
echo ""
echo "🎉 部署完成！"
echo "================================"
echo "🌐 访问地址:"
echo "   HTTP:  http://localhost"
echo "   HTTPS: https://localhost"
echo ""
echo "📊 管理命令:"
echo "   查看状态: docker-compose ps"
echo "   查看日志: docker-compose logs -f"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart"
echo ""
echo "🔧 配置文件位置:"
echo "   应用配置: ./accounts.json"
echo "   自动登录: ./auto_login_config.json"
echo "   代理配置: ./proxy_list.json"
echo "   状态文件: ./status.json"
echo ""
echo "📝 日志文件位置:"
echo "   应用日志: ./logs/"
echo "   Nginx日志: ./logs/nginx/"
echo ""

# 运行测试
if command -v python3 &> /dev/null; then
    echo "🧪 运行部署测试..."
    python3 test_deployment.py http://localhost
fi 