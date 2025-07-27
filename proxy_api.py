#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理IP API获取模块
从指定API获取代理IP并自动配置
"""

import requests
import json
import time
import re
from typing import List, Dict, Optional
from proxy_config import ProxyManager

class ProxyAPI:
    def __init__(self):
        # 代理API配置
        self.api_url = "http://api.xiequ.cn/VAD/GetIp.aspx"
        self.api_params = {
            "act": "getturn51",
            "uid": "134007",
            "vkey": "418D4364313F3B358FCEE5F2B19389BA",
            "num": "1",
            "time": "6",
            "plat": "1",
            "re": "0",
            "type": "7",
            "so": "1",
            "group": "51",
            "ow": "1",
            "spl": "1",
            "addr": "",
            "db": "1"
        }
        self.proxy_manager = ProxyManager()
    
    def get_proxy_from_api(self) -> Optional[Dict]:
        """从API获取代理IP"""
        try:
            print(f"🔄 从API获取代理IP: {self.api_url}")
            
            response = requests.get(self.api_url, params=self.api_params, timeout=10)
            
            if response.status_code == 200:
                content = response.text.strip()
                print(f"API返回内容: {content}")
                
                # 解析返回的代理IP
                proxy_info = self.parse_proxy_response(content)
                if proxy_info:
                    print(f"✅ 成功获取代理: {proxy_info['ip']}:{proxy_info['port']}")
                    return proxy_info
                else:
                    print("❌ 无法解析代理IP")
            else:
                print(f"❌ API请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 获取代理IP失败: {e}")
        
        return None
    
    def parse_proxy_response(self, content: str) -> Optional[Dict]:
        """解析API返回的代理IP"""
        try:
            # 尝试不同的解析方式
            
            # 方式1: 直接是IP:PORT格式
            if re.match(r'^\d+\.\d+\.\d+\.\d+:\d+$', content):
                ip, port = content.split(':')
                return {
                    "ip": ip,
                    "port": int(port),
                    "type": "http",
                    "username": "",
                    "password": ""
                }
            
            # 方式2: JSON格式
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    # 查找IP和端口字段
                    ip = data.get('ip') or data.get('proxy_ip') or data.get('host')
                    port = data.get('port') or data.get('proxy_port')
                    
                    if ip and port:
                        return {
                            "ip": ip,
                            "port": int(port),
                            "type": "http",
                            "username": data.get('username', ''),
                            "password": data.get('password', '')
                        }
            except json.JSONDecodeError:
                pass
            
            # 方式3: 其他格式，尝试正则匹配
            ip_pattern = r'(\d+\.\d+\.\d+\.\d+)'
            port_pattern = r':(\d+)'
            
            ip_match = re.search(ip_pattern, content)
            port_match = re.search(port_pattern, content)
            
            if ip_match and port_match:
                return {
                    "ip": ip_match.group(1),
                    "port": int(port_match.group(1)),
                    "type": "http",
                    "username": "",
                    "password": ""
                }
            
            # 方式4: 如果内容包含多个IP，取第一个
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if re.match(r'^\d+\.\d+\.\d+\.\d+:\d+$', line):
                    ip, port = line.split(':')
                    return {
                        "ip": ip,
                        "port": int(port),
                        "type": "http",
                        "username": "",
                        "password": ""
                    }
            
            print(f"无法解析的API响应格式: {content}")
            return None
            
        except Exception as e:
            print(f"解析代理响应失败: {e}")
            return None
    
    def test_proxy(self, proxy_info: Dict) -> bool:
        """测试代理是否可用"""
        try:
            proxy_url = f"http://{proxy_info['ip']}:{proxy_info['port']}"
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            
            print(f"🧪 测试代理: {proxy_url}")
            response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 代理测试成功: {result}")
                return True
            else:
                print(f"❌ 代理测试失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 代理测试异常: {e}")
            return False
    
    def add_proxy_to_manager(self, proxy_info: Dict):
        """将代理添加到管理器"""
        try:
            self.proxy_manager.add_proxy(
                ip=proxy_info['ip'],
                port=proxy_info['port'],
                username=proxy_info.get('username', ''),
                password=proxy_info.get('password', ''),
                proxy_type=proxy_info.get('type', 'http')
            )
            print(f"✅ 代理已添加到管理器: {proxy_info['ip']}:{proxy_info['port']}")
        except Exception as e:
            print(f"❌ 添加代理到管理器失败: {e}")
    
    def auto_update_proxy(self, max_retries: int = 3):
        """自动更新代理"""
        print("🔄 开始自动更新代理...")
        
        for attempt in range(max_retries):
            print(f"尝试 {attempt + 1}/{max_retries}")
            
            # 获取代理
            proxy_info = self.get_proxy_from_api()
            if not proxy_info:
                print("获取代理失败，等待重试...")
                time.sleep(5)
                continue
            
            # 测试代理
            if self.test_proxy(proxy_info):
                # 添加到管理器
                self.add_proxy_to_manager(proxy_info)
                print("✅ 代理更新成功")
                return True
            else:
                print("代理测试失败，尝试下一个...")
                time.sleep(2)
        
        print("❌ 所有尝试都失败")
        return False
    
    def get_and_test_proxy(self) -> Optional[Dict]:
        """获取并测试代理"""
        proxy_info = self.get_proxy_from_api()
        if proxy_info and self.test_proxy(proxy_info):
            return proxy_info
        return None

def main():
    """测试代理API"""
    api = ProxyAPI()
    
    print("🔧 代理API测试工具")
    print("=" * 50)
    
    while True:
        print("\n1. 获取代理IP")
        print("2. 测试代理")
        print("3. 自动更新代理")
        print("4. 查看代理列表")
        print("0. 退出")
        
        choice = input("\n请选择操作 (0-4): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            proxy = api.get_proxy_from_api()
            if proxy:
                print(f"获取到代理: {proxy}")
            else:
                print("获取代理失败")
        elif choice == "2":
            proxy = api.get_proxy_from_api()
            if proxy:
                if api.test_proxy(proxy):
                    print("代理测试成功")
                else:
                    print("代理测试失败")
            else:
                print("获取代理失败")
        elif choice == "3":
            api.auto_update_proxy()
        elif choice == "4":
            api.proxy_manager.list_proxies()
        else:
            print("无效选择")

if __name__ == "__main__":
    main() 