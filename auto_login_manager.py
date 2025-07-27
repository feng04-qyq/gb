#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动登录管理器
支持多个账号的自动登录，每天自动登录一次，集成IP代理支持
"""

import json
import time
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple

# 导入随机UA库
try:
    from fake_useragent import UserAgent
    UA_AVAILABLE = True
    ua = UserAgent()
except ImportError:
    UA_AVAILABLE = False
    print("警告: fake-useragent库未安装，将使用默认User-Agent")

def get_random_user_agent() -> str:
    """获取随机User-Agent"""
    if UA_AVAILABLE:
        try:
            return ua.random
        except Exception as e:
            print(f"生成随机UA失败: {e}")
            return get_default_user_agent()
    else:
        return get_default_user_agent()

def get_default_user_agent() -> str:
    """获取默认User-Agent"""
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class AutoLoginManager:
    def __init__(self, config_file: str = "auto_login_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
        # 导入代理相关模块
        try:
            from account_proxy_manager import get_proxy_config_for_account, mark_account_proxy_failed, mark_account_proxy_success, refresh_account_proxy
            self.proxy_available = True
            self.get_proxy_config_for_account = get_proxy_config_for_account
            self.mark_account_proxy_failed = mark_account_proxy_failed
            self.mark_account_proxy_success = mark_account_proxy_success
            self.refresh_account_proxy = refresh_account_proxy
        except ImportError:
            self.proxy_available = False
            print("警告: 代理模块不可用，自动登录将使用直接连接")
    
    def load_config(self) -> Dict:
        """加载自动登录配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 兼容旧版本配置
                    if "accounts" not in config:
                        # 如果有单个账号配置，转换为多账号格式
                        if config.get("account") and config.get("password"):
                            config["accounts"] = [{
                                "account": config["account"],
                                "password": config["password"],
                                "enabled": config.get("auto_login_enabled", False),
                                "last_login_date": config.get("last_login_date", "")
                            }]
                        else:
                            config["accounts"] = []
                        config["auto_login_enabled"] = config.get("auto_login_enabled", False)
                    return config
            else:
                return {
                    "auto_login_enabled": False,
                    "accounts": []
                }
        except Exception as e:
            print(f"加载自动登录配置失败: {e}")
            return {
                "auto_login_enabled": False,
                "accounts": []
            }
    
    def save_config(self):
        """保存自动登录配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存自动登录配置失败: {e}")
    
    def add_account(self, account: str, password: str, enabled: bool = True) -> bool:
        """添加自动登录账号"""
        try:
            # 检查账号是否已存在
            for acc in self.config.get("accounts", []):
                if acc["account"] == account:
                    print(f"账号 {account} 已存在")
                    return False
            
            # 添加新账号
            new_account = {
                "account": account,
                "password": password,
                "enabled": enabled,
                "last_login_date": ""
            }
            
            if "accounts" not in self.config:
                self.config["accounts"] = []
            
            self.config["accounts"].append(new_account)
            self.save_config()
            print(f"已添加自动登录账号: {account}")
            return True
        except Exception as e:
            print(f"添加账号失败: {e}")
            return False
    
    def remove_account(self, account: str) -> bool:
        """移除自动登录账号"""
        try:
            accounts = self.config.get("accounts", [])
            for i, acc in enumerate(accounts):
                if acc["account"] == account:
                    del accounts[i]
                    self.save_config()
                    print(f"已移除自动登录账号: {account}")
                    return True
            print(f"账号 {account} 不存在")
            return False
        except Exception as e:
            print(f"移除账号失败: {e}")
            return False
    
    def update_account(self, account: str, password: str = None, enabled: bool = None) -> bool:
        """更新账号信息"""
        try:
            accounts = self.config.get("accounts", [])
            for acc in accounts:
                if acc["account"] == account:
                    if password is not None:
                        acc["password"] = password
                    if enabled is not None:
                        acc["enabled"] = enabled
                    self.save_config()
                    print(f"已更新账号: {account}")
                    return True
            print(f"账号 {account} 不存在")
            return False
        except Exception as e:
            print(f"更新账号失败: {e}")
            return False
    
    def get_accounts(self) -> List[Dict]:
        """获取所有账号"""
        return self.config.get("accounts", [])
    
    def get_enabled_accounts(self) -> List[Dict]:
        """获取所有启用的账号"""
        return [acc for acc in self.config.get("accounts", []) if acc.get("enabled", False)]
    
    def get_login_credentials(self) -> Optional[Dict]:
        """获取需要登录的凭据（兼容旧版本）"""
        enabled_accounts = self.get_enabled_accounts()
        if not enabled_accounts:
            return None
        
        # 返回第一个需要登录的账号
        for acc in enabled_accounts:
            if self.should_account_login(acc):
                return {
                    "account": acc["account"],
                    "password": acc["password"]
                }
        return None
    
    def get_all_login_credentials(self) -> List[Dict]:
        """获取所有需要登录的凭据"""
        credentials = []
        enabled_accounts = self.get_enabled_accounts()
        
        for acc in enabled_accounts:
            if self.should_account_login(acc):
                credentials.append({
                    "account": acc["account"],
                    "password": acc["password"]
                })
        
        return credentials
    
    def should_account_login(self, account_info: Dict) -> bool:
        """判断指定账号是否应该登录"""
        if not account_info.get("enabled", False):
            return False
        
        last_login_date = account_info.get("last_login_date", "")
        today = time.strftime('%Y-%m-%d')
        
        # 如果今天还没有登录过，则应该自动登录
        return last_login_date != today
    
    def should_auto_login(self) -> bool:
        """判断是否应该自动登录（兼容旧版本）"""
        return len(self.get_all_login_credentials()) > 0
    
    def update_account_login_date(self, account: str):
        """更新指定账号的登录日期"""
        try:
            accounts = self.config.get("accounts", [])
            for acc in accounts:
                if acc["account"] == account:
                    acc["last_login_date"] = time.strftime('%Y-%m-%d')
                    self.save_config()
                    print(f"已更新账号 {account} 的登录日期")
                    return True
            print(f"账号 {account} 不存在")
            return False
        except Exception as e:
            print(f"更新登录日期失败: {e}")
            return False
    
    def update_last_login_date(self):
        """更新最后登录日期（兼容旧版本）"""
        # 更新所有启用的账号的登录日期
        enabled_accounts = self.get_enabled_accounts()
        for acc in enabled_accounts:
            acc["last_login_date"] = time.strftime('%Y-%m-%d')
        self.save_config()
    
    def enable_auto_login(self):
        """启用自动登录"""
        self.config["auto_login_enabled"] = True
        self.save_config()
        print("已启用自动登录")
        return True
    
    def disable_auto_login(self):
        """禁用自动登录"""
        self.config["auto_login_enabled"] = False
        self.save_config()
        print("已禁用自动登录")
    
    def enable_account(self, account: str) -> bool:
        """启用指定账号的自动登录"""
        return self.update_account(account, enabled=True)
    
    def disable_account(self, account: str) -> bool:
        """禁用指定账号的自动登录"""
        return self.update_account(account, enabled=False)
    
    def clear_all_credentials(self):
        """清除所有保存的凭据"""
        self.config["accounts"] = []
        self.config["auto_login_enabled"] = False
        self.save_config()
        print("已清除所有保存的登录凭据")
    
    def get_status(self) -> Dict:
        """获取自动登录状态"""
        accounts = self.get_accounts()
        enabled_accounts = self.get_enabled_accounts()
        need_login_accounts = self.get_all_login_credentials()
        
        return {
            "auto_login_enabled": self.config.get("auto_login_enabled", False),
            "total_accounts": len(accounts),
            "enabled_accounts": len(enabled_accounts),
            "need_login_accounts": len(need_login_accounts),
            "accounts": accounts,
            "should_auto_login": self.should_auto_login(),
            "has_credentials": len(accounts) > 0
        }

    def make_login_request_with_proxy(self, account: str, password: str, max_retries: int = 10) -> Tuple[bool, Dict]:
        """使用代理发送登录请求，支持失败重试
        - 网络错误：自动重试（最多max_retries次）
        - 代理错误：持续重试直至成功或达到最大重试次数
        - 账号密码错误：不重试，直接返回失败
        """
        if not self.proxy_available:
            # 如果没有代理模块，使用直接连接
            return self._make_direct_login_request(account, password)
        
        # 构建登录请求数据
        login_data = {
            "account": account,
            "password": password
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": get_random_user_agent()
        }
        
        attempt = 0
        max_attempts = max_retries * 2  # 增加最大尝试次数，因为代理错误会持续重试
        
        while attempt < max_attempts:
            try:
                # 获取账号专用代理
                proxy_config = self.get_proxy_config_for_account(account)
                
                # 发送请求
                if proxy_config:
                    print(f"账号 {account} 使用代理登录 (尝试 {attempt + 1}): {proxy_config.get('http', '')}")
                    response = requests.post(
                        "https://qy.doufp.com/api/auth/login",
                        data=login_data,
                        headers=headers,
                        proxies=proxy_config,
                        timeout=30
                    )
                else:
                    print(f"账号 {account} 直接连接登录 (尝试 {attempt + 1})")
                    response = requests.post(
                        "https://qy.doufp.com/api/auth/login",
                        data=login_data,
                        headers=headers,
                        timeout=30
                    )
                
                # 检查响应
                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0 and result.get("data", {}).get("token"):
                        # 登录成功，标记代理成功
                        if proxy_config:
                            self.mark_account_proxy_success(account)
                        print(f"账号 {account} 登录成功")
                        return True, result
                    else:
                        # 登录失败（账号密码错误等）- 不重试
                        print(f"账号 {account} 登录失败: {result.get('msg', '未知错误')}")
                        if proxy_config:
                            self.mark_account_proxy_failed(account)
                        return False, result
                else:
                    # HTTP错误 - 网络问题，需要重试
                    print(f"账号 {account} HTTP错误: {response.status_code}")
                    if proxy_config:
                        self.mark_account_proxy_failed(account)
                    
            except requests.exceptions.ProxyError as e:
                print(f"账号 {account} 代理连接失败 (尝试 {attempt + 1}): {e}")
                if proxy_config:
                    self.mark_account_proxy_failed(account)
                    # 代理错误：持续重试，尝试刷新代理
                    if self.refresh_account_proxy(account):
                        print(f"账号 {account} 代理已刷新，继续重试...")
                        attempt += 1
                        continue
                    else:
                        print(f"账号 {account} 无法刷新代理，尝试直接连接...")
                        # 尝试直接连接
                        try:
                            response = requests.post(
                                "https://qy.doufp.com/api/auth/login",
                                data=login_data,
                                headers=headers,
                                timeout=30
                            )
                            if response.status_code == 200:
                                result = response.json()
                                if result.get("code") == 0 and result.get("data", {}).get("token"):
                                    print(f"账号 {account} 直接连接登录成功")
                                    return True, result
                                else:
                                    # 账号密码错误，不重试
                                    print(f"账号 {account} 直接连接登录失败: {result.get('msg', '未知错误')}")
                                    return False, result
                            else:
                                # HTTP错误，继续重试
                                print(f"账号 {account} 直接连接HTTP错误: {response.status_code}")
                        except Exception as direct_e:
                            print(f"账号 {account} 直接连接也失败: {direct_e}")
                            # 直接连接也失败，继续重试
                
            except requests.exceptions.RequestException as e:
                print(f"账号 {account} 网络请求失败 (尝试 {attempt + 1}): {e}")
                if proxy_config:
                    self.mark_account_proxy_failed(account)
                # 网络错误：需要重试
            
            except requests.exceptions.Timeout as e:
                print(f"账号 {account} 请求超时 (尝试 {attempt + 1}): {e}")
                if proxy_config:
                    self.mark_account_proxy_failed(account)
                # 超时错误：需要重试
            
            except requests.exceptions.ConnectionError as e:
                print(f"账号 {account} 连接错误 (尝试 {attempt + 1}): {e}")
                if proxy_config:
                    self.mark_account_proxy_failed(account)
                # 连接错误：需要重试
            
            except Exception as e:
                print(f"账号 {account} 未知错误 (尝试 {attempt + 1}): {e}")
                if proxy_config:
                    self.mark_account_proxy_failed(account)
                # 未知错误：需要重试
            
            # 增加尝试次数
            attempt += 1
            
            # 等待一段时间后重试（递增等待时间）
            if attempt < max_attempts:
                wait_time = min(attempt * 2, 30)  # 最大等待30秒
                print(f"账号 {account} 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        print(f"账号 {account} 登录失败，已尝试 {attempt} 次")
        return False, {"code": -1, "msg": "登录失败，已尝试多次"}
    
    def make_login_request_with_retry_until_success(self, account: str, password: str, max_retries: int = 20) -> Tuple[bool, Dict]:
        """使用代理发送登录请求，持续重试直至成功
        - 网络错误：持续重试
        - 代理错误：持续重试
        - 账号密码错误：不重试，直接返回失败
        - 只有在达到最大重试次数或账号密码错误时才停止
        """
        if not self.proxy_available:
            # 如果没有代理模块，使用直接连接
            return self._make_direct_login_request(account, password)
        
        # 构建登录请求数据
        login_data = {
            "account": account,
            "password": password
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": get_random_user_agent()
        }
        
        attempt = 0
        
        while attempt < max_retries:
            try:
                # 获取账号专用代理
                proxy_config = self.get_proxy_config_for_account(account)
                
                # 发送请求
                if proxy_config:
                    print(f"账号 {account} 使用代理登录 (尝试 {attempt + 1}/{max_retries}): {proxy_config.get('http', '')}")
                    response = requests.post(
                        "https://qy.doufp.com/api/auth/login",
                        data=login_data,
                        headers=headers,
                        proxies=proxy_config,
                        timeout=30
                    )
                else:
                    print(f"账号 {account} 直接连接登录 (尝试 {attempt + 1}/{max_retries})")
                    response = requests.post(
                        "https://qy.doufp.com/api/auth/login",
                        data=login_data,
                        headers=headers,
                        timeout=30
                    )
                
                # 检查响应
                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0 and result.get("data", {}).get("token"):
                        # 登录成功，标记代理成功
                        if proxy_config:
                            self.mark_account_proxy_success(account)
                        print(f"账号 {account} 登录成功")
                        return True, result
                    else:
                        # 登录失败（账号密码错误等）- 不重试
                        print(f"账号 {account} 登录失败: {result.get('msg', '未知错误')}")
                        if proxy_config:
                            self.mark_account_proxy_failed(account)
                        return False, result
                else:
                    # HTTP错误 - 网络问题，需要重试
                    print(f"账号 {account} HTTP错误: {response.status_code}")
                    if proxy_config:
                        self.mark_account_proxy_failed(account)
                    
            except requests.exceptions.ProxyError as e:
                print(f"账号 {account} 代理连接失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if proxy_config:
                    self.mark_account_proxy_failed(account)
                    # 代理错误：持续重试，尝试刷新代理
                    if self.refresh_account_proxy(account):
                        print(f"账号 {account} 代理已刷新，继续重试...")
                        attempt += 1
                        continue
                    else:
                        print(f"账号 {account} 无法刷新代理，尝试直接连接...")
                        # 尝试直接连接
                        try:
                            response = requests.post(
                                "https://qy.doufp.com/api/auth/login",
                                data=login_data,
                                headers=headers,
                                timeout=30
                            )
                            if response.status_code == 200:
                                result = response.json()
                                if result.get("code") == 0 and result.get("data", {}).get("token"):
                                    print(f"账号 {account} 直接连接登录成功")
                                    return True, result
                                else:
                                    # 账号密码错误，不重试
                                    print(f"账号 {account} 直接连接登录失败: {result.get('msg', '未知错误')}")
                                    return False, result
                            else:
                                # HTTP错误，继续重试
                                print(f"账号 {account} 直接连接HTTP错误: {response.status_code}")
                        except Exception as direct_e:
                            print(f"账号 {account} 直接连接也失败: {direct_e}")
                            # 直接连接也失败，继续重试
                
            except (requests.exceptions.RequestException, 
                   requests.exceptions.Timeout, 
                   requests.exceptions.ConnectionError) as e:
                print(f"账号 {account} 网络错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if proxy_config:
                    self.mark_account_proxy_failed(account)
                # 网络错误：需要重试
            
            except Exception as e:
                print(f"账号 {account} 未知错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if proxy_config:
                    self.mark_account_proxy_failed(account)
                # 未知错误：需要重试
            
            # 增加尝试次数
            attempt += 1
            
            # 等待一段时间后重试（递增等待时间）
            if attempt < max_retries:
                wait_time = min(attempt * 3, 60)  # 最大等待60秒
                print(f"账号 {account} 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        print(f"账号 {account} 登录失败，已尝试 {attempt} 次")
        return False, {"code": -1, "msg": "登录失败，已尝试多次"}
    
    def _make_direct_login_request(self, account: str, password: str) -> Tuple[bool, Dict]:
        """直接连接登录请求（无代理）"""
        try:
            login_data = {
                "account": account,
                "password": password
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": get_random_user_agent()
            }
            
            response = requests.post(
                "https://qy.doufp.com/api/auth/login",
                data=login_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0 and result.get("data", {}).get("token"):
                    print(f"账号 {account} 直接连接登录成功")
                    return True, result
                else:
                    print(f"账号 {account} 登录失败: {result.get('msg', '未知错误')}")
                    return False, result
            else:
                print(f"账号 {account} HTTP错误: {response.status_code}")
                return False, {"code": -1, "msg": f"HTTP错误: {response.status_code}"}
                
        except Exception as e:
            print(f"账号 {account} 直接连接失败: {e}")
            return False, {"code": -1, "msg": f"连接失败: {e}"}
    
    def auto_login_account(self, account: str, password: str, retry_until_success: bool = False) -> bool:
        """自动登录指定账号（带代理重试）
        
        Args:
            account: 账号
            password: 密码
            retry_until_success: 是否持续重试直至成功（默认False，使用有限重试）
        """
        print(f"开始自动登录账号: {account}")
        
        if retry_until_success:
            # 使用持续重试机制
            success, result = self.make_login_request_with_retry_until_success(account, password, max_retries=20)
        else:
            # 使用有限重试机制
            success, result = self.make_login_request_with_proxy(account, password, max_retries=10)
        
        if success:
            # 登录成功，更新登录日期
            self.update_account_login_date(account)
            print(f"账号 {account} 自动登录成功")
            return True
        else:
            print(f"账号 {account} 自动登录失败: {result.get('msg', '未知错误')}")
            return False
    
    def auto_login_all_accounts(self, retry_until_success: bool = False) -> Dict[str, bool]:
        """自动登录所有启用的账号
        
        Args:
            retry_until_success: 是否持续重试直至成功（默认False，使用有限重试）
        """
        results = {}
        enabled_accounts = self.get_enabled_accounts()
        
        if not enabled_accounts:
            print("没有启用的自动登录账号")
            return results
        
        print(f"开始自动登录 {len(enabled_accounts)} 个账号...")
        
        for account_info in enabled_accounts:
            account = account_info["account"]
            password = account_info["password"]
            
            # 检查是否需要登录
            if self.should_account_login(account_info):
                success = self.auto_login_account(account, password, retry_until_success)
                results[account] = success
            else:
                print(f"账号 {account} 今天已经登录过，跳过")
                results[account] = True  # 标记为成功（已登录）
        
        return results

# 全局自动登录管理器实例
auto_login_manager = AutoLoginManager()

def add_auto_login_account(account: str, password: str, enabled: bool = True) -> bool:
    """添加自动登录账号（便捷函数）"""
    return auto_login_manager.add_account(account, password, enabled)

def remove_auto_login_account(account: str) -> bool:
    """移除自动登录账号（便捷函数）"""
    return auto_login_manager.remove_account(account)

def get_auto_login_accounts() -> List[Dict]:
    """获取所有自动登录账号（便捷函数）"""
    return auto_login_manager.get_accounts()

def get_enabled_auto_login_accounts() -> List[Dict]:
    """获取所有启用的自动登录账号（便捷函数）"""
    return auto_login_manager.get_enabled_accounts()

def should_auto_login() -> bool:
    """判断是否应该自动登录（便捷函数）"""
    return auto_login_manager.should_auto_login()

def get_login_credentials() -> Optional[Dict]:
    """获取登录凭据（便捷函数，兼容旧版本）"""
    return auto_login_manager.get_login_credentials()

def get_all_login_credentials() -> List[Dict]:
    """获取所有需要登录的凭据（便捷函数）"""
    return auto_login_manager.get_all_login_credentials()

def update_account_login_date(account: str):
    """更新指定账号的登录日期（便捷函数）"""
    return auto_login_manager.update_account_login_date(account)

def update_last_login_date():
    """更新最后登录日期（便捷函数，兼容旧版本）"""
    auto_login_manager.update_last_login_date()

def get_auto_login_status() -> Dict:
    """获取自动登录状态（便捷函数）"""
    return auto_login_manager.get_status()

def auto_login_account(account: str, password: str, retry_until_success: bool = False) -> bool:
    """自动登录指定账号（便捷函数）"""
    return auto_login_manager.auto_login_account(account, password, retry_until_success)

def auto_login_all_accounts(retry_until_success: bool = False) -> Dict[str, bool]:
    """自动登录所有启用的账号（便捷函数）"""
    return auto_login_manager.auto_login_all_accounts(retry_until_success)

def make_login_request_with_proxy(account: str, password: str, max_retries: int = 10) -> Tuple[bool, Dict]:
    """使用代理发送登录请求（便捷函数）"""
    return auto_login_manager.make_login_request_with_proxy(account, password, max_retries)

def make_login_request_with_retry_until_success(account: str, password: str, max_retries: int = 20) -> Tuple[bool, Dict]:
    """使用代理发送登录请求，持续重试直至成功（便捷函数）"""
    return auto_login_manager.make_login_request_with_retry_until_success(account, password, max_retries)

if __name__ == "__main__":
    # 测试自动登录管理器
    manager = AutoLoginManager()
    
    print("🔧 多账号自动登录管理器测试")
    print("=" * 50)
    
    # 测试添加账号
    print("1. 测试添加账号...")
    manager.add_account("test1", "pass1", True)
    manager.add_account("test2", "pass2", True)
    manager.add_account("test3", "pass3", False)
    
    # 测试获取状态
    print("\n2. 测试获取状态...")
    status = manager.get_status()
    print(f"状态: {status}")
    
    # 测试获取需要登录的账号
    print("\n3. 测试获取需要登录的账号...")
    credentials = manager.get_all_login_credentials()
    print(f"需要登录的账号: {len(credentials)} 个")
    for cred in credentials:
        print(f"  - {cred['account']}")
    
    # 测试更新登录日期
    print("\n4. 测试更新登录日期...")
    manager.update_account_login_date("test1")
    
    # 再次获取需要登录的账号
    credentials = manager.get_all_login_credentials()
    print(f"更新后需要登录的账号: {len(credentials)} 个")
    for cred in credentials:
        print(f"  - {cred['account']}")
    
    # 测试移除账号
    print("\n5. 测试移除账号...")
    manager.remove_account("test2")
    
    # 最终状态
    print("\n6. 最终状态...")
    status = manager.get_status()
    print(f"最终状态: {status}") 