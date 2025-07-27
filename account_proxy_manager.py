#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账号代理管理器
为每个账号分配独立的代理IP，避免账号关联
"""

import json
import random
import time
from typing import Dict, List, Optional
from proxy_api import ProxyAPI

class AccountProxyManager:
    def __init__(self, mapping_file: str = "account_proxy_mapping.json"):
        self.mapping_file = mapping_file
        self.proxy_api = ProxyAPI()
        self.account_proxy_map = self.load_mapping()
    
    def load_mapping(self) -> Dict:
        """加载账号代理映射"""
        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_mapping(self):
        """保存账号代理映射"""
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            json.dump(self.account_proxy_map, f, ensure_ascii=False, indent=2)
    
    def get_proxy_for_account(self, account: str) -> Optional[Dict]:
        """为指定账号获取代理"""
        # 如果账号已有代理，返回现有代理
        if account in self.account_proxy_map:
            proxy_info = self.account_proxy_map[account]
            # 检查代理是否仍然有效
            if self.is_proxy_valid(proxy_info):
                return proxy_info
        
        # 为账号分配新代理
        return self.assign_new_proxy_to_account(account)
    
    def assign_new_proxy_to_account(self, account: str) -> Optional[Dict]:
        """为账号分配新代理"""
        try:
            print(f"为账号 {account} 分配新代理...")
            
            # 从API获取新代理
            proxy_info = self.proxy_api.get_and_test_proxy()
            if not proxy_info:
                print(f"无法为账号 {account} 获取代理")
                return None
            
            # 保存到映射
            self.account_proxy_map[account] = proxy_info
            self.save_mapping()
            
            print(f"账号 {account} 分配代理: {proxy_info['ip']}:{proxy_info['port']}")
            return proxy_info
            
        except Exception as e:
            print(f"为账号 {account} 分配代理失败: {e}")
            return None
    
    def is_proxy_valid(self, proxy_info: Dict) -> bool:
        """检查代理是否有效"""
        try:
            # 简单的有效性检查：代理信息完整且失败次数不多
            if not proxy_info or 'ip' not in proxy_info or 'port' not in proxy_info:
                return False
            
            # 如果失败次数过多，认为无效
            if proxy_info.get('fail_count', 0) >= 3:
                return False
            
            return True
        except:
            return False
    
    def mark_proxy_failed(self, account: str):
        """标记账号代理失败"""
        if account in self.account_proxy_map:
            proxy_info = self.account_proxy_map[account]
            proxy_info['fail_count'] = proxy_info.get('fail_count', 0) + 1
            self.save_mapping()
            print(f"账号 {account} 代理失败，失败次数: {proxy_info['fail_count']}")
    
    def mark_proxy_success(self, account: str):
        """标记账号代理成功"""
        if account in self.account_proxy_map:
            proxy_info = self.account_proxy_map[account]
            proxy_info['fail_count'] = 0
            proxy_info['last_used'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self.save_mapping()
    
    def refresh_account_proxy(self, account: str) -> Optional[Dict]:
        """刷新账号代理"""
        try:
            print(f"刷新账号 {account} 的代理...")
            
            # 获取新代理
            proxy_info = self.proxy_api.get_and_test_proxy()
            if not proxy_info:
                return None
            
            # 更新映射
            self.account_proxy_map[account] = proxy_info
            self.save_mapping()
            
            print(f"账号 {account} 代理已刷新: {proxy_info['ip']}:{proxy_info['port']}")
            return proxy_info
            
        except Exception as e:
            print(f"刷新账号 {account} 代理失败: {e}")
            return None
    
    def get_all_account_proxies(self) -> Dict:
        """获取所有账号的代理信息"""
        return self.account_proxy_map.copy()
    
    def remove_account_proxy(self, account: str):
        """移除账号代理"""
        if account in self.account_proxy_map:
            del self.account_proxy_map[account]
            self.save_mapping()
            print(f"已移除账号 {account} 的代理")
    
    def get_proxy_config_for_account(self, account: str) -> Optional[Dict]:
        """获取账号的代理配置"""
        proxy_info = self.get_proxy_for_account(account)
        if not proxy_info:
            return None
        
        proxy_url = f"{proxy_info['type']}://{proxy_info['ip']}:{proxy_info['port']}"
        return {
            "http": proxy_url,
            "https": proxy_url
        }
    
    def list_all_mappings(self):
        """列出所有账号代理映射"""
        print("账号代理映射:")
        for account, proxy_info in self.account_proxy_map.items():
            status = "✅" if self.is_proxy_valid(proxy_info) else "❌"
            print(f"{account}: {status} {proxy_info['ip']}:{proxy_info['port']} "
                  f"(失败: {proxy_info.get('fail_count', 0)})")

# 全局账号代理管理器实例
account_proxy_manager = AccountProxyManager()

def get_proxy_for_account(account: str) -> Optional[Dict]:
    """为账号获取代理（便捷函数）"""
    return account_proxy_manager.get_proxy_for_account(account)

def get_proxy_config_for_account(account: str) -> Optional[Dict]:
    """获取账号代理配置（便捷函数）"""
    return account_proxy_manager.get_proxy_config_for_account(account)

def mark_account_proxy_failed(account: str):
    """标记账号代理失败（便捷函数）"""
    account_proxy_manager.mark_proxy_failed(account)

def mark_account_proxy_success(account: str):
    """标记账号代理成功（便捷函数）"""
    account_proxy_manager.mark_proxy_success(account)

def refresh_account_proxy(account: str) -> Optional[Dict]:
    """刷新账号代理（便捷函数）"""
    return account_proxy_manager.refresh_account_proxy(account)

if __name__ == "__main__":
    # 测试账号代理管理器
    manager = AccountProxyManager()
    
    print("🔧 账号代理管理器测试")
    print("=" * 50)
    
    # 测试为账号分配代理
    test_account = "test123"
    proxy = manager.get_proxy_for_account(test_account)
    if proxy:
        print(f"测试账号 {test_account} 分配代理成功: {proxy['ip']}:{proxy['port']}")
    else:
        print(f"测试账号 {test_account} 分配代理失败")
    
    # 列出所有映射
    manager.list_all_mappings() 