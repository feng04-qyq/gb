# 重试机制和随机UA系统

## 概述

本系统实现了强大的网络错误自动重试机制和随机User-Agent功能，确保在各种网络环境下都能稳定运行。

## 重试机制

### 1. 有限重试模式

- **适用场景**: 一般网络请求，避免无限重试
- **重试次数**: 默认10次，可配置
- **等待策略**: 递增等待时间（2秒、4秒、6秒...最大30秒）
- **停止条件**: 
  - 达到最大重试次数
  - 账号密码错误（不重试）
  - 登录成功

### 2. 持续重试模式

- **适用场景**: 重要操作，必须成功
- **重试次数**: 默认20次，可配置
- **等待策略**: 递增等待时间（3秒、6秒、9秒...最大60秒）
- **停止条件**: 
  - 达到最大重试次数
  - 账号密码错误（不重试）
  - 登录成功

### 3. 错误类型处理

#### 网络错误（自动重试）
- `requests.exceptions.RequestException`
- `requests.exceptions.Timeout`
- `requests.exceptions.ConnectionError`
- HTTP状态码错误（非200）

#### 代理错误（持续重试）
- `requests.exceptions.ProxyError`
- 自动刷新代理
- 代理失败时尝试直接连接

#### 账号密码错误（不重试）
- 登录API返回错误码
- 直接返回失败，不进行重试

## 随机User-Agent系统

### 1. 功能特性

- **自动生成**: 使用`fake-useragent`库生成真实浏览器UA
- **备用方案**: 如果在线UA获取失败，使用预定义UA列表
- **一致性**: 所有API请求都使用随机UA
- **性能优化**: UA生成速度快，不影响请求性能

### 2. UA类型

#### 在线UA（优先）
- Chrome浏览器（桌面/移动）
- Firefox浏览器
- Safari浏览器（桌面/移动）
- Edge浏览器
- 各种移动设备UA

#### 备用UA列表
```python
FALLBACK_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
]
```

## 使用方法

### 1. 自动登录重试

#### 有限重试
```python
from auto_login_manager import auto_login_account

# 使用有限重试模式
success = auto_login_account("account", "password", retry_until_success=False)
```

#### 持续重试
```python
# 使用持续重试模式
success = auto_login_account("account", "password", retry_until_success=True)
```

### 2. 批量登录重试

```python
from auto_login_manager import auto_login_all_accounts

# 有限重试
results = auto_login_all_accounts(retry_until_success=False)

# 持续重试
results = auto_login_all_accounts(retry_until_success=True)
```

### 3. 手动触发重试

#### 前端API调用
```javascript
// 有限重试
fetch('/api/trigger_auto_login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({retry_until_success: false})
});

// 持续重试
fetch('/api/trigger_auto_login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({retry_until_success: true})
});
```

### 4. 获取随机UA

```python
from auto_login_manager import get_random_user_agent
from app import get_random_ua

# 两种方式都可以
ua1 = get_random_user_agent()
ua2 = get_random_ua()
```

## 配置选项

### 1. 重试配置

```python
# 修改重试次数
success, result = make_login_request_with_proxy(account, password, max_retries=15)
success, result = make_login_request_with_retry_until_success(account, password, max_retries=30)
```

### 2. 等待时间配置

当前等待时间策略：
- 有限重试: `min(attempt * 2, 30)` 秒
- 持续重试: `min(attempt * 3, 60)` 秒

## 监控和日志

### 1. 重试日志

系统会记录详细的重试信息：
```
账号 test_account 使用代理登录 (尝试 1): http://proxy1:8080
账号 test_account 代理连接失败 (尝试 1): ProxyError
账号 test_account 代理已刷新，继续重试...
账号 test_account 等待 3 秒后重试...
账号 test_account 登录成功
```

### 2. UA使用日志

每次请求都会使用新的随机UA，在日志中可以看到：
```
使用UA: Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 Mobile/15E148 Safari/604.1
```

## 性能测试结果

### UA生成性能
- 生成100个UA耗时: ~0.23秒
- UA唯一性: 约65-70%（20个UA中13-14个唯一）
- 内存占用: 极低

### 重试机制性能
- 网络错误重试: 快速响应
- 代理错误重试: 自动切换，无缝连接
- 等待时间: 递增策略，避免服务器压力

## 故障排除

### 1. UA生成失败

**症状**: 使用默认UA
**解决方案**: 
- 检查网络连接
- 确认`fake-useragent`库已安装
- 查看备用UA是否正常工作

### 2. 重试失败

**症状**: 达到最大重试次数仍失败
**可能原因**:
- 网络连接问题
- 代理服务器问题
- 目标服务器问题
- 账号密码错误

**解决方案**:
- 检查网络连接
- 更新代理列表
- 验证账号密码
- 增加重试次数

### 3. 性能问题

**症状**: 请求响应慢
**解决方案**:
- 调整等待时间策略
- 优化代理选择
- 减少重试次数

## 最佳实践

1. **选择合适的重试模式**
   - 一般操作使用有限重试
   - 重要操作使用持续重试

2. **监控重试频率**
   - 避免过于频繁的重试
   - 合理设置等待时间

3. **定期更新代理**
   - 保持代理池健康
   - 及时清理失效代理

4. **日志分析**
   - 定期检查重试日志
   - 识别常见错误模式

## 更新日志

### v1.0.0
- 实现基础重试机制
- 添加随机UA功能
- 支持有限重试和持续重试模式
- 集成代理错误处理
- 添加详细日志记录 