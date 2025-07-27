# IBOX管理系统 - 部署说明

## 🚀 快速部署

### Windows用户
```bash
# 双击运行部署脚本
deploy.bat
```

### Linux/Mac用户
```bash
# 给脚本执行权限
chmod +x quick_deploy.sh

# 运行部署脚本
./quick_deploy.sh
```

### 服务器部署
```bash
# 1. 上传项目文件到服务器
scp -r /path/to/your/withdraw_web/* root@your-server-ip:/opt/ibox-management/

# 2. 连接到服务器
ssh root@your-server-ip
cd /opt/ibox-management

# 3. 运行部署脚本
chmod +x deploy.sh
./deploy.sh

# 4. 启动服务
systemctl start ibox-management
```

## 📋 部署前准备

### 1. 安装Docker
- **Windows**: 下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux**: 运行 `curl -fsSL https://get.docker.com | sh`
- **Mac**: 下载并安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

### 2. 安装Docker Compose
- **Windows/Mac**: Docker Desktop已包含
- **Linux**: `sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose`

### 3. 检查安装
```bash
docker --version
docker-compose --version
```

## 🔧 手动部署步骤

### 1. 创建目录结构
```bash
mkdir -p logs/nginx ssl data
```

### 2. 生成SSL证书
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem -out ssl/cert.pem \
    -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
```

### 3. 构建和启动
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps
```

## 🌐 访问系统

部署成功后，可以通过以下地址访问：

- **HTTP**: http://localhost
- **HTTPS**: https://localhost (推荐)

## 📊 管理命令

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f ibox-app
docker-compose logs -f nginx
```

### 重启服务
```bash
docker-compose restart
```

### 停止服务
```bash
docker-compose down
```

### 更新服务
```bash
docker-compose pull
docker-compose up -d
```

## 🧪 测试部署

运行测试脚本验证部署是否成功：

```bash
python test_deployment.py http://localhost
```

## 📁 文件说明

### 核心文件
- `app.py` - Flask应用主文件
- `requirements.txt` - Python依赖
- `templates/` - HTML模板文件

### 部署文件
- `Dockerfile` - Docker镜像构建
- `docker-compose.yml` - 容器编排
- `nginx.conf` - Nginx配置
- `start.sh` - 启动脚本

### 配置文件
- `accounts.json` - 账户配置
- `auto_login_config.json` - 自动登录配置
- `proxy_list.json` - 代理列表
- `status.json` - 系统状态

### 部署脚本
- `deploy.bat` - Windows部署脚本
- `quick_deploy.sh` - Linux/Mac快速部署
- `deploy.sh` - 服务器生产部署
- `test_deployment.py` - 部署测试

## 🔒 安全配置

### SSL证书
- 开发环境使用自签名证书
- 生产环境建议使用Let's Encrypt证书

### 防火墙
- 开放端口: 80, 443
- 关闭不必要的端口

### 访问控制
- 配置IP白名单
- 设置基本认证

## 📈 性能优化

### 系统要求
- **最低**: 1核CPU, 2GB内存, 20GB存储
- **推荐**: 2核CPU, 4GB内存, 50GB SSD

### 优化建议
- 使用SSD存储
- 配置足够的内存
- 启用Gzip压缩
- 定期清理日志

## 🚨 故障排除

### 常见问题

#### 1. 端口被占用
```bash
# 查看端口占用
netstat -tulpn | grep :80
netstat -tulpn | grep :443

# 停止占用端口的服务
sudo systemctl stop apache2  # 如果Apache占用80端口
```

#### 2. 权限问题
```bash
# 设置文件权限
chmod 644 *.json
chmod +x start.sh
```

#### 3. SSL证书问题
```bash
# 重新生成证书
rm -f ssl/*
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem -out ssl/cert.pem \
    -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
```

#### 4. 容器启动失败
```bash
# 查看详细错误
docker-compose logs ibox-app

# 检查配置文件
docker-compose config
```

### 获取帮助

1. 查看日志文件
2. 运行测试脚本
3. 检查系统资源
4. 查看Docker状态

## 📞 技术支持

### 文档资源
- `DEPLOYMENT_GUIDE.md` - 详细部署指南
- `DEPLOYMENT_SUMMARY.md` - 部署总结
- `SYSTEM_SUMMARY.md` - 系统功能总结

### 测试工具
- `test_deployment.py` - 部署测试
- `test_*.py` - 功能测试

---

## 🎉 部署成功！

恭喜您成功部署IBOX管理系统！

### 下一步操作
1. 访问 https://localhost
2. 配置账户信息
3. 设置自动登录
4. 测试系统功能
5. 监控系统运行

**祝您使用愉快！** 🚀 