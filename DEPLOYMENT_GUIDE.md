# IBOX管理系统部署指南

## 🚀 快速部署

### 1. 服务器要求

#### 最低配置
- **CPU**: 1核心
- **内存**: 2GB RAM
- **存储**: 20GB 可用空间
- **网络**: 稳定的互联网连接

#### 推荐配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 50GB SSD
- **网络**: 100Mbps带宽

#### 操作系统支持
- Ubuntu 18.04+
- CentOS 7+
- Debian 9+
- Red Hat Enterprise Linux 7+

### 2. 自动部署（推荐）

#### 步骤1: 准备服务器
```bash
# 连接到服务器
ssh root@your-server-ip

# 下载部署脚本
wget https://raw.githubusercontent.com/your-repo/ibox-management/main/deploy.sh
chmod +x deploy.sh
```

#### 步骤2: 运行部署脚本
```bash
# 执行自动部署
./deploy.sh
```

#### 步骤3: 上传项目文件
```bash
# 创建项目目录
mkdir -p /opt/ibox-management
cd /opt/ibox-management

# 上传项目文件（使用scp或git clone）
scp -r /path/to/your/project/* root@your-server-ip:/opt/ibox-management/
```

#### 步骤4: 启动服务
```bash
# 启动服务
systemctl start ibox-management

# 检查状态
systemctl status ibox-management

# 查看日志
docker-compose logs -f
```

### 3. 手动部署

#### 步骤1: 安装Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# CentOS/RHEL
yum install -y docker
systemctl start docker
systemctl enable docker
```

#### 步骤2: 安装Docker Compose
```bash
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

#### 步骤3: 创建项目目录
```bash
mkdir -p /opt/ibox-management
cd /opt/ibox-management
```

#### 步骤4: 上传项目文件
```bash
# 上传所有项目文件到此目录
# 确保包含以下文件：
# - app.py
# - requirements.txt
# - Dockerfile
# - docker-compose.yml
# - nginx.conf
# - start.sh
# - templates/
# - 其他Python模块文件
```

#### 步骤5: 生成SSL证书
```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem -out ssl/cert.pem \
    -subj "/C=CN/ST=State/L=City/O=Organization/CN=your-domain.com"
```

#### 步骤6: 构建和启动
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 🔧 配置说明

### 1. 环境变量配置

创建 `.env` 文件：
```bash
# 应用配置
FLASK_ENV=production
FLASK_APP=app.py
SECRET_KEY=your-secret-key-here

# 数据库配置（如果使用）
DATABASE_URL=sqlite:///ibox.db

# 代理配置
PROXY_API_URL=http://api.xiequ.cn/VAD/GetIp.aspx

# 时区配置
TZ=Asia/Shanghai
```

### 2. Nginx配置

#### 自定义域名
编辑 `nginx.conf` 中的 `server_name`：
```nginx
server_name your-domain.com www.your-domain.com;
```

#### SSL证书
替换自签名证书为Let's Encrypt证书：
```bash
# 安装certbot
apt install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 证书会自动配置到nginx
```

### 3. 防火墙配置

```bash
# UFW (Ubuntu)
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Firewalld (CentOS)
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

## 📊 监控和维护

### 1. 服务管理

```bash
# 启动服务
systemctl start ibox-management

# 停止服务
systemctl stop ibox-management

# 重启服务
systemctl restart ibox-management

# 查看状态
systemctl status ibox-management

# 查看日志
journalctl -u ibox-management -f
```

### 2. Docker管理

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f ibox-app
docker-compose logs -f nginx

# 重启服务
docker-compose restart

# 更新镜像
docker-compose pull
docker-compose up -d
```

### 3. 数据备份

```bash
# 备份配置文件
tar -czf backup-$(date +%Y%m%d).tar.gz \
    accounts.json \
    auto_login_config.json \
    proxy_list.json \
    account_proxy_mapping.json \
    status.json

# 备份日志
tar -czf logs-$(date +%Y%m%d).tar.gz logs/
```

### 4. 性能监控

```bash
# 查看系统资源
htop
df -h
free -h

# 查看Docker资源使用
docker stats

# 查看网络连接
netstat -tulpn | grep :80
netstat -tulpn | grep :443
```

## 🔒 安全配置

### 1. SSL/TLS配置

#### 使用Let's Encrypt（推荐）
```bash
# 安装certbot
apt install certbot python3-certbot-nginx

# 获取免费SSL证书
certbot --nginx -d your-domain.com

# 自动续期
crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

#### 手动配置SSL
```bash
# 生成强密钥
openssl genrsa -out ssl/private.key 4096

# 生成证书签名请求
openssl req -new -key ssl/private.key -out ssl/cert.csr

# 从CA获取证书后，配置nginx
```

### 2. 安全头配置

在 `nginx.conf` 中添加安全头：
```nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
```

### 3. 访问控制

#### IP白名单
```nginx
# 在nginx配置中添加
allow 192.168.1.0/24;
allow 10.0.0.0/8;
deny all;
```

#### 基本认证
```bash
# 生成密码文件
htpasswd -c /etc/nginx/.htpasswd username

# 在nginx配置中添加
auth_basic "Restricted Access";
auth_basic_user_file /etc/nginx/.htpasswd;
```

## 🚨 故障排除

### 1. 常见问题

#### 容器启动失败
```bash
# 查看详细错误
docker-compose logs ibox-app

# 检查端口占用
netstat -tulpn | grep :5000

# 检查配置文件
docker-compose config
```

#### 网络连接问题
```bash
# 检查防火墙
ufw status
firewall-cmd --list-all

# 检查DNS解析
nslookup your-domain.com

# 检查SSL证书
openssl s_client -connect your-domain.com:443
```

#### 性能问题
```bash
# 查看资源使用
docker stats

# 查看日志大小
du -sh logs/

# 清理日志
docker-compose exec ibox-app find /app/logs -name "*.log" -mtime +7 -delete
```

### 2. 日志分析

#### 应用日志
```bash
# 查看错误日志
docker-compose logs ibox-app | grep ERROR

# 查看访问日志
tail -f logs/access.log

# 实时监控
docker-compose logs -f --tail=100 ibox-app
```

#### Nginx日志
```bash
# 查看访问日志
tail -f logs/nginx/access.log

# 查看错误日志
tail -f logs/nginx/error.log

# 分析访问统计
awk '{print $1}' logs/nginx/access.log | sort | uniq -c | sort -nr
```

### 3. 性能优化

#### 数据库优化
```bash
# 如果使用SQLite，定期优化
docker-compose exec ibox-app sqlite3 /app/data/ibox.db "VACUUM;"
```

#### 缓存优化
```bash
# 清理Docker缓存
docker system prune -a

# 清理日志
docker-compose exec ibox-app find /app/logs -name "*.log" -mtime +30 -delete
```

## 📈 扩展部署

### 1. 负载均衡

#### 使用HAProxy
```bash
# 安装HAProxy
apt install haproxy

# 配置负载均衡
# 参考HAProxy官方文档
```

#### 使用Nginx负载均衡
```nginx
upstream ibox_backend {
    server 192.168.1.10:5000;
    server 192.168.1.11:5000;
    server 192.168.1.12:5000;
}
```

### 2. 高可用部署

#### 使用Docker Swarm
```bash
# 初始化Swarm
docker swarm init

# 部署服务
docker stack deploy -c docker-compose.yml ibox
```

#### 使用Kubernetes
```bash
# 创建Kubernetes部署文件
# 参考Kubernetes官方文档
```

## 📞 技术支持

### 1. 日志收集
```bash
# 收集系统信息
uname -a
cat /etc/os-release
docker version
docker-compose version

# 收集应用日志
docker-compose logs > app-logs.txt
docker-compose logs nginx > nginx-logs.txt
```

### 2. 问题报告
请提供以下信息：
- 操作系统版本
- Docker版本
- 错误日志
- 复现步骤
- 期望行为

### 3. 联系方式
- GitHub Issues: [项目地址]
- 邮箱: support@example.com
- 文档: [文档地址]

---

**部署完成！** 🎉

访问 https://your-domain.com 开始使用IBOX管理系统。 