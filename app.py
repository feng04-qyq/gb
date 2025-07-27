from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import json
import os
import time
import random
from fake_useragent import UserAgent

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于session
ACCOUNTS_FILE = "accounts.json"
STATUS_FILE = "status.json"
LOG_FILE = "sign_log.txt"

# 初始化随机UA生成器
try:
    ua = UserAgent()
    UA_AVAILABLE = True
except Exception as e:
    # 如果无法获取在线UA数据，使用备用UA列表
    ua = None
    UA_AVAILABLE = False
    print(f"警告: 无法初始化UserAgent: {e}")
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

def get_random_ua():
    """获取随机User-Agent"""
    try:
        if UA_AVAILABLE and ua:
            return ua.random
        else:
            return random.choice(FALLBACK_UAS)
    except Exception as e:
        # 如果都失败了，返回默认UA
        print(f"生成随机UA失败: {e}")
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def random_delay():
    """随机延迟，避免请求过于频繁"""
    time.sleep(random.uniform(0.5, 2.0))

# 导入代理管理器
try:
    from proxy_config import proxy_manager, get_proxy_config, make_request_with_proxy
    from proxy_api import ProxyAPI
    from account_proxy_manager import account_proxy_manager, get_proxy_config_for_account, mark_account_proxy_failed, mark_account_proxy_success, refresh_account_proxy
    from auto_login_manager import auto_login_manager, add_auto_login_account, remove_auto_login_account, get_auto_login_accounts, get_enabled_auto_login_accounts, should_auto_login, get_login_credentials, get_all_login_credentials, update_account_login_date, update_last_login_date, get_auto_login_status, auto_login_account, auto_login_all_accounts
except ImportError:
    # 如果代理模块不存在，使用简单的代理配置
    def get_proxy_config():
        """获取代理配置"""
        # 从环境变量或配置文件读取代理设置
        proxy_ip = os.getenv('PROXY_IP', '')  # 例如: "127.0.0.1:8080"
        proxy_username = os.getenv('PROXY_USERNAME', '')
        proxy_password = os.getenv('PROXY_PASSWORD', '')
        
        if not proxy_ip:
            return None
        
        # 构建代理URL
        if proxy_username and proxy_password:
            proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_ip}"
        else:
            proxy_url = f"http://{proxy_ip}"
        
        return {
            "http": proxy_url,
            "https": proxy_url
        }

    def make_request_with_proxy(method, url, **kwargs):
        """使用代理发送请求"""
        proxy_config = get_proxy_config()
        
        if proxy_config:
            kwargs['proxies'] = proxy_config
            log(f"使用代理发送请求: {method} {url} 代理: {proxy_config['http']}")
        else:
            log(f"直接发送请求: {method} {url}")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, **kwargs)
            else:
                raise ValueError(f"不支持的请求方法: {method}")
            
            return response
        except requests.exceptions.ProxyError as e:
            log(f"代理连接失败: {e}")
            # 如果代理失败，尝试直接连接
            if proxy_config:
                log("尝试直接连接...")
                kwargs.pop('proxies', None)
                if method.upper() == 'GET':
                    return requests.get(url, **kwargs)
                elif method.upper() == 'POST':
                    return requests.post(url, **kwargs)
            raise
        except Exception as e:
            log(f"请求失败: {e}")
            raise

def make_request_with_account_proxy(method, url, account, **kwargs):
    """使用账号专用代理发送请求"""
    try:
        # 获取账号专用代理
        proxy_config = get_proxy_config_for_account(account)
        
        if proxy_config:
            kwargs['proxies'] = proxy_config
            log(f"账号 {account} 使用代理发送请求: {method} {url} 代理: {proxy_config['http']}")
        else:
            log(f"账号 {account} 直接发送请求: {method} {url}")
        
        if method.upper() == 'GET':
            response = requests.get(url, **kwargs)
        elif method.upper() == 'POST':
            response = requests.post(url, **kwargs)
        else:
            raise ValueError(f"不支持的请求方法: {method}")
        
        # 请求成功，标记代理成功
        mark_account_proxy_success(account)
        
        return response
        
    except requests.exceptions.ProxyError as e:
        log(f"账号 {account} 代理连接失败: {e}")
        mark_account_proxy_failed(account)
        
        # 尝试刷新代理并重试
        if refresh_account_proxy(account):
            log(f"账号 {account} 代理已刷新，重试请求...")
            return make_request_with_account_proxy(method, url, account, **kwargs)
        else:
            # 如果无法刷新代理，尝试直接连接
            log(f"账号 {account} 无法获取代理，尝试直接连接...")
            kwargs.pop('proxies', None)
            if method.upper() == 'GET':
                return requests.get(url, **kwargs)
            elif method.upper() == 'POST':
                return requests.post(url, **kwargs)
                
    except Exception as e:
        log(f"账号 {account} 请求失败: {e}")
        raise

# 全局代理API实例
proxy_api = None
try:
    proxy_api = ProxyAPI()
except Exception as e:
    log(f"初始化代理API失败: {e}")

def update_proxy_from_api(max_retries=5):
    """从API更新代理，支持多次重试"""
    global proxy_api
    if not proxy_api:
        return False
    
    for attempt in range(max_retries):
        try:
            log(f"开始从API更新代理... (尝试 {attempt + 1}/{max_retries})")
            if proxy_api.auto_update_proxy():
                log("代理更新成功")
                return True
            else:
                log(f"代理更新失败 (尝试 {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待2秒后重试
                    continue
        except Exception as e:
            log(f"更新代理异常 (尝试 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
    
    log("所有代理更新尝试都失败")
    return False

def force_update_proxy_on_failure():
    """在请求失败时强制更新代理"""
    log("检测到请求失败，强制更新代理...")
    return update_proxy_from_api(max_retries=3)

def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_status(status):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")

def login_api(account, password):
    login_url = "https://qy.doufp.com/api/auth/login"
    headers = {
        "content-type": "application/json;charset=UTF-8",
        "user-agent": get_random_ua()
    }
    data = {"account": account, "captcha": "", "key": None, "password": password}
    
    # 使用账号专用代理
    try:
        random_delay()
        resp = make_request_with_account_proxy('POST', login_url, account, headers=headers, json=data, timeout=15)
        return resp.json()
    except Exception as e:
        log(f"账号 {account} 登录API请求失败: {e}")
        return {"code": -1, "msg": f"网络请求失败: {e}"}

def sign_api(token, account=None):
    sign_url = "https://qy.doufp.com/api/user/sign"
    headers = {
        "content-type": "application/json;charset=UTF-8",
        "user-agent": get_random_ua(),
        "authorization": token
    }
    
    # 使用账号专用代理
    try:
        random_delay()
        if account:
            resp = make_request_with_account_proxy('POST', sign_url, account, headers=headers, json={}, timeout=15)
        else:
            resp = make_request_with_proxy('POST', sign_url, headers=headers, json={}, timeout=15)
        return resp.json()
    except Exception as e:
        log(f"账号 {account} 签到API请求失败: {e}")
        return {"code": -1, "msg": f"网络请求失败: {e}"}

def balance_api(token, account=None):
    url = "https://qy.doufp.com/api/assets/myAssets"
    headers = {
        "authorization": token,
        "content-type": "application/json;charset=UTF-8",
        "user-agent": get_random_ua()
    }
    
    # 使用账号专用代理
    try:
        random_delay()
        if account:
            resp = make_request_with_account_proxy('GET', url, account, headers=headers, timeout=15)
        else:
            resp = make_request_with_proxy('GET', url, headers=headers, timeout=15)
        data = resp.json()
        print('balance_api返回:', data)
        # 查找 name_en 为 income_wallet 的资产（coinList）
        coin_list = data.get('data', {}).get('coinList', [])
        balance = 0
        for asset in coin_list:
            if asset.get('name_en') == 'income_wallet':
                try:
                    balance = float(asset.get('num', 0))
                except Exception:
                    balance = 0
                break
        return {'balance': balance, 'raw': data}
    except Exception as e:
        log(f"账号 {account} 余额API请求失败: {e}")
        return {'balance': 0, 'raw': {}, 'error': str(e)}

def withdraw_api(token, num, coin_type="income_wallet", withdraw_password="", account=None):
    url = "https://qy.doufp.com/api/assets/withdraw"
    headers = {
        "authorization": token,
        "content-type": "application/json;charset=UTF-8",
        "user-agent": get_random_ua()
    }
    payload = {
        "coin_type": coin_type,
        "num": num,
        "password": withdraw_password
    }
    
    # 使用账号专用代理
    try:
        random_delay()
        if account:
            resp = make_request_with_account_proxy('POST', url, account, headers=headers, json=payload, timeout=15)
        else:
            resp = make_request_with_proxy('POST', url, headers=headers, json=payload, timeout=15)
        return resp.json()
    except Exception as e:
        log(f"账号 {account} 提现API请求失败: {e}")
        return {"code": -1, "msg": f"网络请求失败: {e}"}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account = request.form['account']
        password = request.form['password']
        login_json = login_api(account, password)
        token = login_json.get("data", {}).get("token")
        if token:
            session['account'] = account
            session['password'] = password
            session['token'] = token
            
            # 不再自动保存登录信息，用户需要手动设置自动登录凭据
            
            # 更新最后登录日期
            try:
                update_last_login_date()
            except Exception as e:
                log(f"更新登录日期失败: {e}")
            
            # 登录成功后立即签到、查余额、提现
            today = time.strftime('%Y-%m-%d')
            status = load_status()
            # 签到
            sign_result = sign_api(token, account)
            signed = sign_result.get('code') == 0
            sign_msg = sign_result.get('msg', '')
            # 查余额
            balance_json = balance_api(token, account)
            balance = balance_json.get('balance', 0)
            # 提现
            withdraw_result = withdraw_api(token, str(balance), account=account) if balance else {"msg": "无余额"}
            withdraw_status = withdraw_result.get('msg', '')
            # 存储状态
            status[account] = {
                'date': today,
                'signed': signed,
                'sign_msg': sign_msg,
                'balance': balance,
                'withdraw_status': withdraw_status
            }
            save_status(status)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='登录失败，请检查账号密码')
    
    # GET请求：检查是否需要自动登录
    if should_auto_login():
        all_credentials = get_all_login_credentials()
        if all_credentials:
            # 尝试所有需要登录的账号
            for credentials in all_credentials:
                log(f"尝试自动登录: {credentials['account']}")
                
                # 使用新的代理重试机制进行自动登录
                success = auto_login_account(credentials['account'], credentials['password'])
                
                if success:
                    # 登录成功，获取token用于session
                    login_json = login_api(credentials['account'], credentials['password'])
                    token = login_json.get("data", {}).get("token")
                    if token:
                        session['account'] = credentials['account']
                        session['password'] = credentials['password']
                        session['token'] = token
                        
                        log(f"自动登录成功: {credentials['account']}")
                        return redirect(url_for('dashboard'))
                else:
                    log(f"自动登录失败: {credentials['account']}")
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'account' not in session:
        return redirect(url_for('login'))
    account = session['account']
    status = load_status().get(account, {})
    today = time.strftime('%Y-%m-%d')
    signed = status.get('date') == today and status.get('signed', False)
    balance = status.get('balance', '--')
    withdraw_status = status.get('withdraw_status', '--')
    return render_template('sign.html', account=account, signed=signed, balance=balance, withdraw_status=withdraw_status)

@app.route('/api/sign_status')
def api_sign_status():
    if 'account' not in session:
        return jsonify({'error': '未登录'}), 401
    account = session['account']
    status = load_status().get(account, {})
    today = time.strftime('%Y-%m-%d')
    signed = status.get('date') == today and status.get('signed', False)
    return jsonify({'signed': signed})

@app.route('/api/balance')
def api_balance():
    if 'account' not in session:
        return jsonify({'error': '未登录'}), 401
    account = session['account']
    status = load_status().get(account, {})
    balance = status.get('balance', '--')
    return jsonify({'balance': balance})

@app.route('/api/withdraw_status')
def api_withdraw_status():
    if 'account' not in session:
        return jsonify({'error': '未登录'}), 401
    account = session['account']
    status = load_status().get(account, {})
    withdraw_status = status.get('withdraw_status', '--')
    return jsonify({'withdraw_status': withdraw_status})

@app.route('/api/accounts')
def api_accounts():
    accounts = load_accounts()
    status = load_status()
    today = time.strftime('%Y-%m-%d')
    result = []
    for acc in accounts:
        acc_status = status.get(acc['account'], {})
        signed = acc_status.get('date') == today and acc_status.get('signed', False)
        sign_msg = acc_status.get('sign_msg', '')
        balance = acc_status.get('balance', '--')
        withdraw_status = acc_status.get('withdraw_status', '--')
        result.append({
            'account': acc['account'],
            'signed': signed,
            'sign_msg': sign_msg,
            'balance': balance,
            'withdraw_status': withdraw_status
        })
    return jsonify({'accounts': result})

@app.route('/api/delete_account', methods=['POST'])
def api_delete_account():
    data = request.json
    account = data.get('account')
    accounts = load_accounts()
    accounts = [a for a in accounts if a['account'] != account]
    save_accounts(accounts)
    # 同时删除状态
    status = load_status()
    if account in status:
        del status[account]
        save_status(status)
    return jsonify({'status': 'ok'})

@app.route('/api/batch_delete', methods=['POST'])
def api_batch_delete():
    data = request.json
    del_accounts = data.get('accounts', [])
    accounts = load_accounts()
    accounts = [a for a in accounts if a['account'] not in del_accounts]
    save_accounts(accounts)
    # 同时删除状态
    status = load_status()
    for acc in del_accounts:
        if acc in status:
            del status[acc]
    save_status(status)
    return jsonify({'status': 'ok'})

@app.route('/api/batch_sign_withdraw', methods=['POST'])
def api_batch_sign_withdraw():
    data = request.json
    batch_accounts = data.get('accounts', [])
    today = time.strftime('%Y-%m-%d')
    status = load_status()
    results = []
    for acc in load_accounts():
        if acc['account'] in batch_accounts:
            account = acc['account']
            password = acc['password']
            login_json = login_api(account, password)
            token = login_json.get("data", {}).get("token")
            if not token:
                results.append({'account': account, 'result': '登录失败'})
                continue
            # 签到
            sign_result = sign_api(token, account)
            signed = sign_result.get('code') == 0
            sign_msg = sign_result.get('msg', '')
            # 查余额
            balance_json = balance_api(token, account)
            balance = balance_json.get('balance', 0)
            # 提现
            withdraw_result = withdraw_api(token, str(balance), account=account) if balance else {"msg": "无余额"}
            withdraw_status = withdraw_result.get('msg', '')
            # 存储状态
            status[account] = {
                'date': today,
                'signed': signed,
                'sign_msg': sign_msg,
                'balance': balance,
                'withdraw_status': withdraw_status
            }
            save_status(status)
            results.append({'account': account, 'result': f"签到:{'成功' if signed else '失败'}({sign_msg}) 余额:{balance} 提现:{withdraw_status}"})
    return jsonify({'results': results})

@app.route("/add_account", methods=["POST"])
def add_account():
    data = request.json
    account = data["account"]
    password = data["password"]
    
    # 添加账号前先验证账号是否可用（使用代理）
    try:
        log(f"验证新账号: {account}")
        login_json = login_api(account, password)
        token = login_json.get("data", {}).get("token")
        if not token:
            return jsonify({"status": "error", "msg": "账号验证失败，请检查账号密码"})
        
        # 验证成功，保存账号
        accounts = load_accounts()
        accounts.append({"account": account, "password": password})
        save_accounts(accounts)
        
        log(f"账号 {account} 添加成功")
        return jsonify({"status": "ok", "msg": "账号添加成功"})
        
    except Exception as e:
        log(f"添加账号异常: {e}")
        return jsonify({"status": "error", "msg": f"添加账号失败: {e}"})

def auto_sign_and_withdraw():
    """定时任务：自动签到、查余额、提现"""
    global TASK_STATUS
    
    TASK_STATUS["is_running"] = True
    TASK_STATUS["last_run"] = time.strftime('%Y-%m-%d %H:%M:%S')
    TASK_STATUS["total_accounts"] = 0
    TASK_STATUS["success_count"] = 0
    TASK_STATUS["error_count"] = 0
    
    try:
        # 任务开始前自动更新代理
        log("定时任务开始，尝试更新代理...")
        update_proxy_from_api()
        
        accounts = load_accounts()
        today = time.strftime('%Y-%m-%d')
        status = load_status()
        
        log(f"开始定时任务，共 {len(accounts)} 个账号")
        
        for acc in accounts:
            TASK_STATUS["total_accounts"] += 1
            account = acc['account']
            password = acc['password']
            
            try:
                login_json = login_api(account, password)
                token = login_json.get("data", {}).get("token")
                if not token:
                    log(f"{account} 自动登录失败: {login_json}")
                    TASK_STATUS["error_count"] += 1
                    continue
                
                # 签到
                sign_result = sign_api(token, account)
                signed = sign_result.get('code') == 0
                sign_msg = sign_result.get('msg', '')
                
                # 查余额
                balance_json = balance_api(token, account)
                balance = balance_json.get('balance', 0)
                
                # 提现
                withdraw_result = withdraw_api(token, str(balance), account=account) if balance else {"msg": "无余额"}
                withdraw_status = withdraw_result.get('msg', '')
                
                # 存储状态
                status[account] = {
                    'date': today,
                    'signed': signed,
                    'sign_msg': sign_msg,
                    'balance': balance,
                    'withdraw_status': withdraw_status
                }
                save_status(status)
                
                log(f"{account} 自动签到:{'成功' if signed else '失败'}({sign_msg}) 余额:{balance} 提现:{withdraw_status}")
                
                if signed:
                    TASK_STATUS["success_count"] += 1
                else:
                    TASK_STATUS["error_count"] += 1
                    
            except Exception as e:
                log(f"{account} 处理异常: {e}")
                TASK_STATUS["error_count"] += 1
        
        log(f"定时任务完成，成功: {TASK_STATUS['success_count']}, 失败: {TASK_STATUS['error_count']}")
        
    except Exception as e:
        log(f"定时任务异常: {e}")
    finally:
        TASK_STATUS["is_running"] = False

# 定时任务：每天00:30自动签到、查余额、提现
scheduler = BackgroundScheduler()
scheduler.add_job(auto_sign_and_withdraw, "cron", hour=0, minute=30, id="daily_sign_withdraw")
scheduler.start()

# 记录定时任务状态
TASK_STATUS = {
    "last_run": None,
    "next_run": None,
    "is_running": False,
    "total_accounts": 0,
    "success_count": 0,
    "error_count": 0
}

@app.route("/api/task_status")
def api_task_status():
    """获取定时任务状态"""
    global TASK_STATUS
    # 获取下次运行时间
    job = scheduler.get_job("daily_sign_withdraw")
    if job:
        TASK_STATUS["next_run"] = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None
    
    return jsonify(TASK_STATUS)

@app.route("/api/manual_task", methods=['POST'])
def api_manual_task():
    """手动触发定时任务"""
    global TASK_STATUS
    if TASK_STATUS["is_running"]:
        return jsonify({"status": "error", "msg": "任务正在运行中"})
    
    try:
        # 异步执行任务
        import threading
        thread = threading.Thread(target=auto_sign_and_withdraw)
        thread.daemon = True
        thread.start()
        return jsonify({"status": "ok", "msg": "任务已启动"})
    except Exception as e:
        return jsonify({"status": "error", "msg": f"启动失败: {e}"})

@app.route("/api/task_log")
def api_task_log():
    """获取最近的日志"""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # 返回最近50行日志
            recent_logs = lines[-50:] if len(lines) > 50 else lines
            return jsonify({"logs": recent_logs})
    except Exception as e:
        return jsonify({"logs": [], "error": str(e)})

@app.route("/api/update_proxy", methods=['POST'])
def api_update_proxy():
    """从API更新代理"""
    if 'account' not in session:
        return jsonify({"status": "error", "msg": "未登录"}), 401
    
    try:
        success = update_proxy_from_api()
        if success:
            return jsonify({"status": "ok", "msg": "代理更新成功"})
        else:
            return jsonify({"status": "error", "msg": "代理更新失败"})
    except Exception as e:
        return jsonify({"status": "error", "msg": f"更新异常: {e}"})

@app.route("/api/proxy_status")
def api_proxy_status():
    """获取代理状态"""
    if 'account' not in session:
        return jsonify({"status": "error", "msg": "未登录"}), 401
    
    try:
        from proxy_config import proxy_manager
        proxies = proxy_manager.proxy_list
        available_count = len([p for p in proxies if p.get('enabled', True)])
        total_count = len(proxies)
        
        # 获取当前正在使用的代理（优先显示API获取的代理）
        current_proxy = None
        if proxy_manager.current_proxy:
            # 如果有当前代理，显示它
            current_proxy = proxy_manager.current_proxy
        elif proxies:
            # 否则显示第一个可用的代理
            for proxy in proxies:
                if proxy.get('enabled', True) and proxy.get('fail_count', 0) < 3:
                    current_proxy = proxy
                    break
        
        # 获取账号代理映射
        account_proxies = account_proxy_manager.get_all_account_proxies()
        
        return jsonify({
            "total": total_count,
            "available": available_count,
            "current_proxy": current_proxy,
            "proxies": proxies,
            "account_proxies": account_proxies
        })
    except Exception as e:
        return jsonify({"status": "error", "msg": f"获取状态失败: {e}"})

@app.route("/api/account_proxy_status")
def api_account_proxy_status():
    """获取账号代理状态"""
    if 'account' not in session:
        return jsonify({"status": "error", "msg": "未登录"}), 401
    
    try:
        account_proxies = account_proxy_manager.get_all_account_proxies()
        return jsonify({
            "account_proxies": account_proxies
        })
    except Exception as e:
        return jsonify({"status": "error", "msg": f"获取账号代理状态失败: {e}"})

@app.route("/api/auto_login_status")
def api_auto_login_status():
    """获取自动登录状态"""
    try:
        status = get_auto_login_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"status": "error", "msg": f"获取自动登录状态失败: {e}"})

@app.route("/api/auto_login_control", methods=['POST'])
def api_auto_login_control():
    """控制自动登录功能"""
    if 'account' not in session:
        return jsonify({"status": "error", "msg": "未登录"}), 401
    
    try:
        data = request.json
        action = data.get('action')
        target_account = data.get('account', '')  # 目标账号（可选）
        
        if action == 'enable':
            if target_account:
                # 启用指定账号
                success = auto_login_manager.enable_account(target_account)
                if success:
                    return jsonify({"status": "ok", "msg": f"已启用账号 {target_account} 的自动登录"})
                else:
                    return jsonify({"status": "error", "msg": f"账号 {target_account} 不存在"})
            else:
                # 启用全局自动登录
                success = auto_login_manager.enable_auto_login()
                if success:
                    return jsonify({"status": "ok", "msg": "已启用自动登录"})
                else:
                    return jsonify({"status": "error", "msg": "请先添加自动登录账号"})
        elif action == 'disable':
            if target_account:
                # 禁用指定账号
                success = auto_login_manager.disable_account(target_account)
                if success:
                    return jsonify({"status": "ok", "msg": f"已禁用账号 {target_account} 的自动登录"})
                else:
                    return jsonify({"status": "error", "msg": f"账号 {target_account} 不存在"})
            else:
                # 禁用全局自动登录
                auto_login_manager.disable_auto_login()
                return jsonify({"status": "ok", "msg": "已禁用自动登录"})
        elif action == 'clear':
            if target_account:
                # 移除指定账号
                success = auto_login_manager.remove_account(target_account)
                if success:
                    return jsonify({"status": "ok", "msg": f"已移除账号 {target_account}"})
                else:
                    return jsonify({"status": "error", "msg": f"账号 {target_account} 不存在"})
            else:
                # 清除所有凭据
                auto_login_manager.clear_all_credentials()
                return jsonify({"status": "ok", "msg": "已清除所有保存的登录凭据"})
        else:
            return jsonify({"status": "error", "msg": "无效的操作"})
    except Exception as e:
        return jsonify({"status": "error", "msg": f"操作失败: {e}"})

@app.route("/api/add_auto_login_account", methods=['POST'])
def api_add_auto_login_account():
    """添加自动登录账号"""
    if 'account' not in session:
        return jsonify({"status": "error", "msg": "未登录"}), 401
    
    try:
        data = request.json
        account = data.get('account', '').strip()
        password = data.get('password', '').strip()
        enabled = data.get('enabled', True)
        
        if not account or not password:
            return jsonify({"status": "error", "msg": "账号和密码不能为空"})
        
        # 验证账号密码是否有效
        login_json = login_api(account, password)
        token = login_json.get("data", {}).get("token")
        if not token:
            return jsonify({"status": "error", "msg": "账号密码验证失败，请检查输入"})
        
        # 添加自动登录账号
        success = add_auto_login_account(account, password, enabled)
        if success:
            return jsonify({"status": "ok", "msg": "自动登录账号添加成功"})
        else:
            return jsonify({"status": "error", "msg": "账号已存在"})
        
    except Exception as e:
        return jsonify({"status": "error", "msg": f"添加失败: {e}"})

@app.route("/api/remove_auto_login_account", methods=['POST'])
def api_remove_auto_login_account():
    """移除自动登录账号"""
    if 'account' not in session:
        return jsonify({"status": "error", "msg": "未登录"}), 401
    
    try:
        data = request.json
        account = data.get('account', '').strip()
        
        if not account:
            return jsonify({"status": "error", "msg": "账号不能为空"})
        
        # 移除自动登录账号
        success = remove_auto_login_account(account)
        if success:
            return jsonify({"status": "ok", "msg": "自动登录账号移除成功"})
        else:
            return jsonify({"status": "error", "msg": "账号不存在"})
        
    except Exception as e:
        return jsonify({"status": "error", "msg": f"移除失败: {e}"})

@app.route("/api/get_auto_login_accounts")
def api_get_auto_login_accounts():
    """获取所有自动登录账号"""
    if 'account' not in session:
        return jsonify({"status": "error", "msg": "未登录"}), 401
    
    try:
        accounts = get_auto_login_accounts()
        return jsonify({"status": "ok", "accounts": accounts})
    except Exception as e:
        return jsonify({"status": "error", "msg": f"获取失败: {e}"})

@app.route("/api/trigger_auto_login", methods=['POST'])
def api_trigger_auto_login():
    """手动触发自动登录"""
    if 'account' not in session:
        return jsonify({"status": "error", "msg": "未登录"}), 401
    
    try:
        data = request.json or {}
        retry_until_success = data.get('retry_until_success', False)
        
        # 触发所有启用的账号自动登录
        results = auto_login_all_accounts(retry_until_success=retry_until_success)
        
        # 统计结果
        total_accounts = len(results)
        success_count = sum(1 for success in results.values() if success)
        failed_count = total_accounts - success_count
        
        # 构建详细结果
        details = []
        for account, success in results.items():
            details.append({
                "account": account,
                "success": success,
                "message": "登录成功" if success else "登录失败"
            })
        
        retry_mode = "持续重试" if retry_until_success else "有限重试"
        return jsonify({
            "status": "ok",
            "msg": f"自动登录完成（{retry_mode}），成功: {success_count}, 失败: {failed_count}",
            "total_accounts": total_accounts,
            "success_count": success_count,
            "failed_count": failed_count,
            "retry_mode": retry_mode,
            "details": details
        })
        
    except Exception as e:
        return jsonify({"status": "error", "msg": f"自动登录失败: {e}"})

@app.route("/task_config")
def task_config():
    """定时任务配置页面"""
    if 'account' not in session:
        return redirect(url_for('login'))
    return render_template('task_config.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/health')
def health_check():
    """健康检查接口"""
    try:
        # 检查基本服务状态
        status = {
            "status": "healthy",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "version": "1.0.0",
            "services": {
                "flask": "running",
                "scheduler": "running" if scheduler.running else "stopped"
            }
        }
        return jsonify(status), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }), 500

if __name__ == "__main__":
    # 开发环境使用debug模式，生产环境使用wsgi.py
    app.run(host='0.0.0.0', port=5000, debug=True)
