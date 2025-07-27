#!/bin/bash

# 设置环境变量
export PYTHONPATH=/app
export FLASK_APP=app.py
export FLASK_ENV=production

# 创建必要的目录
mkdir -p /app/logs
mkdir -p /app/data

# 检查配置文件是否存在，如果不存在则创建默认配置
if [ ! -f /app/accounts.json ]; then
    echo '[]' > /app/accounts.json
fi

if [ ! -f /app/auto_login_config.json ]; then
    echo '{"auto_login_enabled": false, "accounts": []}' > /app/auto_login_config.json
fi

if [ ! -f /app/proxy_list.json ]; then
    echo '[]' > /app/proxy_list.json
fi

if [ ! -f /app/account_proxy_mapping.json ]; then
    echo '{}' > /app/account_proxy_mapping.json
fi

if [ ! -f /app/status.json ]; then
    echo '{"last_sign_time": "", "last_withdraw_time": "", "task_status": "stopped"}' > /app/status.json
fi

# 设置文件权限
chmod 644 /app/*.json
chmod 755 /app/logs
chmod 755 /app/data

# 启动应用
echo "Starting IBOX Management System..."
echo "Environment: $FLASK_ENV"
echo "Python Path: $PYTHONPATH"

# 使用gunicorn启动Flask应用
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --worker-class gevent \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --access-logfile /app/logs/access.log \
    --error-logfile /app/logs/error.log \
    --log-level info \
    app:app 