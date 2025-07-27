#!/bin/bash

# IBOX管理系统部署脚本
# 适用于Ubuntu/CentOS服务器

set -e

echo "🚀 开始部署IBOX管理系统..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}请使用root权限运行此脚本${NC}"
    exit 1
fi

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo -e "${RED}无法检测操作系统${NC}"
    exit 1
fi

echo -e "${GREEN}检测到操作系统: $OS $VER${NC}"

# 更新系统包
echo -e "${YELLOW}更新系统包...${NC}"
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    apt update && apt upgrade -y
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    yum update -y
else
    echo -e "${RED}不支持的操作系统${NC}"
    exit 1
fi

# 安装Docker
echo -e "${YELLOW}安装Docker...${NC}"
if ! command -v docker &> /dev/null; then
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        apt update
        apt install -y docker-ce docker-ce-cli containerd.io
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        yum install -y yum-utils
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y docker-ce docker-ce-cli containerd.io
    fi
    
    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}Docker安装完成${NC}"
else
    echo -e "${GREEN}Docker已安装${NC}"
fi

# 安装Docker Compose
echo -e "${YELLOW}安装Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose安装完成${NC}"
else
    echo -e "${GREEN}Docker Compose已安装${NC}"
fi

# 创建项目目录
PROJECT_DIR="/opt/ibox-management"
echo -e "${YELLOW}创建项目目录: $PROJECT_DIR${NC}"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 创建必要的目录
mkdir -p logs/nginx
mkdir -p ssl
mkdir -p data

# 生成自签名SSL证书（生产环境建议使用Let's Encrypt）
echo -e "${YELLOW}生成SSL证书...${NC}"
if [ ! -f ssl/cert.pem ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem -out ssl/cert.pem \
        -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
    echo -e "${GREEN}SSL证书生成完成${NC}"
else
    echo -e "${GREEN}SSL证书已存在${NC}"
fi

# 设置防火墙
echo -e "${YELLOW}配置防火墙...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    echo -e "${GREEN}UFW防火墙配置完成${NC}"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=ssh
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
    echo -e "${GREEN}Firewalld防火墙配置完成${NC}"
fi

# 创建systemd服务文件
echo -e "${YELLOW}创建systemd服务...${NC}"
cat > /etc/systemd/system/ibox-management.service << EOF
[Unit]
Description=IBOX Management System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
systemctl daemon-reload
systemctl enable ibox-management.service

echo -e "${GREEN}部署脚本执行完成！${NC}"
echo -e "${YELLOW}下一步操作：${NC}"
echo "1. 将项目文件复制到 $PROJECT_DIR"
echo "2. 运行: systemctl start ibox-management"
echo "3. 检查状态: systemctl status ibox-management"
echo "4. 查看日志: docker-compose logs -f" 