#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理配置管理
支持多种代理配置方式
"""

import os
import json
import random
from typing import Dict, List, Optional

class ProxyManager:
    def __init__(self, config_file: str = "proxy_list.json"):
        self.config_file = config_file
        self.proxy_list = self.load_proxy_list()
        self.current_proxy = None
    
    def load_proxy_list(self) -> List[Dict]:
        """加载代理列表"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载代理配置文件失败: {e}")
                return []
        return []
    
    def save_proxy_list(self):
        """保存代理列表"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.proxy_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存代理配置文件失败: {e}")
    
    def add_proxy(self, ip: str, port: int, username: str = "", password: str = "", 
                  proxy_type: str = "http", enabled: bool = True):
        """添加代理"""
        proxy = {
            "ip": ip,
            "port": port,
            "username": username,
            "password": password,
            "type": proxy_type,
            "enabled": enabled,
            "fail_count": 0,
            "last_used": None
        }
        self.proxy_list.append(proxy)
        self.save_proxy_list()
    
    def remove_proxy(self, index: int):
        """删除代理"""
        if 0 <= index < len(self.proxy_list):
            del self.proxy_list[index]
            self.save_proxy_list()
    
    def get_random_proxy(self) -> Optional[Dict]:
        """获取随机可用代理"""
        available_proxies = [p for p in self.proxy_list if p.get('enabled', True)]
        if not available_proxies:
            return None
        
        # 只使用非本地代理（从API获取的代理）
        api_proxies = [p for p in available_proxies if not p['ip'].startswith('127.0.0.1') and not p['ip'].startswith('localhost')]
        
        # 如果没有API代理，返回None
        if not api_proxies:
            print("警告: 没有可用的API代理，尝试更新代理...")
            return None
        
        # 按失败次数排序，优先使用失败次数少的代理
        api_proxies.sort(key=lambda x: x.get('fail_count', 0))
        
        # 从前50%的代理中随机选择
        select_count = max(1, len(api_proxies) // 2)
        selected_proxy = random.choice(api_proxies[:select_count])
        
        self.current_proxy = selected_proxy
        return selected_proxy
    
    def get_proxy_config(self) -> Optional[Dict]:
        """获取当前代理配置"""
        proxy = self.get_random_proxy()
        if not proxy:
            return None
        
        # 构建代理URL
        if proxy.get('username') and proxy.get('password'):
            proxy_url = f"{proxy['type']}://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
        else:
            proxy_url = f"{proxy['type']}://{proxy['ip']}:{proxy['port']}"
        
        return {
            "http": proxy_url,
            "https": proxy_url
        }
    
    def mark_proxy_failed(self, proxy: Dict):
        """标记代理失败"""
        for p in self.proxy_list:
            if p['ip'] == proxy['ip'] and p['port'] == proxy['port']:
                p['fail_count'] = p.get('fail_count', 0) + 1
                # 如果失败次数过多，禁用代理
                if p['fail_count'] >= 5:
                    p['enabled'] = False
                break
        self.save_proxy_list()
    
    def mark_proxy_success(self, proxy: Dict):
        """标记代理成功"""
        for p in self.proxy_list:
            if p['ip'] == proxy['ip'] and p['port'] == proxy['port']:
                p['fail_count'] = 0
                p['last_used'] = None
                break
        self.save_proxy_list()
    
    def list_proxies(self):
        """列出所有代理"""
        print("代理列表:")
        for i, proxy in enumerate(self.proxy_list):
            status = "✅" if proxy.get('enabled', True) else "❌"
            print(f"{i}: {status} {proxy['type']}://{proxy['ip']}:{proxy['port']} "
                  f"(失败: {proxy.get('fail_count', 0)})")
    
    def test_proxy(self, proxy: Dict) -> bool:
        """测试代理是否可用"""
        import requests
        
        proxy_config = {
            "http": f"{proxy['type']}://{proxy['ip']}:{proxy['port']}",
            "https": f"{proxy['type']}://{proxy['ip']}:{proxy['port']}"
        }
        
        if proxy.get('username') and proxy.get('password'):
            proxy_config = {
                "http": f"{proxy['type']}://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}",
                "https": f"{proxy['type']}://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
            }
        
        try:
            response = requests.get("http://httpbin.org/ip", proxies=proxy_config, timeout=10)
            if response.status_code == 200:
                print(f"代理测试成功: {proxy['ip']}:{proxy['port']}")
                return True
        except Exception as e:
            print(f"代理测试失败: {proxy['ip']}:{proxy['port']} - {e}")
        
        return False

# 全局代理管理器实例
proxy_manager = ProxyManager()

def get_proxy_config():
    """获取代理配置（兼容旧接口）"""
    return proxy_manager.get_proxy_config()

def make_request_with_proxy(method, url, **kwargs):
    """使用代理发送请求（增强版）"""
    import requests
    
    proxy_config = get_proxy_config()
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if proxy_config:
                kwargs['proxies'] = proxy_config
                print(f"使用代理发送请求: {method} {url} 代理: {proxy_config['http']}")
            else:
                print(f"直接发送请求: {method} {url}")
            
            if method.upper() == 'GET':
                response = requests.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, **kwargs)
            else:
                raise ValueError(f"不支持的请求方法: {method}")
            
            # 请求成功，标记代理成功
            if proxy_config and proxy_manager.current_proxy:
                proxy_manager.mark_proxy_success(proxy_manager.current_proxy)
            
            return response
            
        except requests.exceptions.ProxyError as e:
            print(f"代理连接失败: {e}")
            # 标记代理失败
            if proxy_manager.current_proxy:
                proxy_manager.mark_proxy_failed(proxy_manager.current_proxy)
            
            retry_count += 1
            if retry_count < max_retries:
                print(f"尝试使用其他代理 (重试 {retry_count}/{max_retries})")
                # 获取新的代理
                proxy_config = get_proxy_config()
                continue
            else:
                print("所有代理都失败，尝试直接连接...")
                kwargs.pop('proxies', None)
                if method.upper() == 'GET':
                    return requests.get(url, **kwargs)
                elif method.upper() == 'POST':
                    return requests.post(url, **kwargs)
                
        except Exception as e:
            print(f"请求失败: {e}")
            # 如果是网络错误且是第一次重试，尝试更新代理
            if retry_count == 0 and ("连接" in str(e) or "timeout" in str(e).lower() or "refused" in str(e).lower()):
                print("检测到网络错误，尝试更新代理...")
                try:
                    # 尝试从API更新代理
                    from proxy_api import ProxyAPI
                    api = ProxyAPI()
                    if api.auto_update_proxy():
                        print("代理更新成功，重试请求...")
                        proxy_config = get_proxy_config()
                        retry_count += 1
                        continue
                except Exception as update_error:
                    print(f"代理更新失败: {update_error}")
            raise

# 示例代理配置
def create_sample_proxy_list():
    """创建示例代理列表"""
    sample_proxies = [
        {
            "ip": "127.0.0.1",
            "port": 8080,
            "username": "",
            "password": "",
            "type": "http",
            "enabled": True,
            "fail_count": 0,
            "last_used": None
        },
        {
            "ip": "127.0.0.1", 
            "port": 1080,
            "username": "",
            "password": "",
            "type": "socks5",
            "enabled": True,
            "fail_count": 0,
            "last_used": None
        }
    ]
    
    with open("proxy_list.json", 'w', encoding='utf-8') as f:
        json.dump(sample_proxies, f, ensure_ascii=False, indent=2)
    
    print("示例代理配置文件已创建: proxy_list.json")

if __name__ == "__main__":
    # 创建示例配置
    create_sample_proxy_list()
    
    # 测试代理管理器
    pm = ProxyManager()
    pm.list_proxies() 