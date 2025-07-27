#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动登录功能演示
展示如何使用新的手动设置自动登录凭据功能
"""

from auto_login_manager import AutoLoginManager
import json

def demo_auto_login_system():
    """演示自动登录系统"""
    print("🎯 自动登录系统演示")
    print("=" * 60)
    
    # 创建管理器实例
    manager = AutoLoginManager()
    
    print("📋 当前状态:")
    status = manager.get_status()
    print(f"   - 启用状态: {status['enabled']}")
    print(f"   - 自动登录: {status['auto_login_enabled']}")
    print(f"   - 保存账号: {status['account'] or '未设置'}")
    print(f"   - 有凭据: {status['has_credentials']}")
    print(f"   - 需要登录: {status['should_auto_login']}")
    
    print("\n🔧 步骤1: 设置自动登录凭据")
    print("-" * 40)
    
    # 模拟用户输入账号密码
    demo_account = "demo_user"
    demo_password = "demo_pass"
    
    print(f"设置凭据: {demo_account}")
    manager.set_auto_login_credentials(demo_account, demo_password)
    
    print("\n📋 设置后的状态:")
    status = manager.get_status()
    print(f"   - 启用状态: {status['enabled']}")
    print(f"   - 自动登录: {status['auto_login_enabled']}")
    print(f"   - 保存账号: {status['account']}")
    print(f"   - 有凭据: {status['has_credentials']}")
    print(f"   - 需要登录: {status['should_auto_login']}")
    
    print("\n🔧 步骤2: 启用自动登录")
    print("-" * 40)
    
    success = manager.enable_auto_login()
    if success:
        print("✅ 自动登录已启用")
    else:
        print("❌ 启用失败")
    
    print("\n📋 启用后的状态:")
    status = manager.get_status()
    print(f"   - 启用状态: {status['enabled']}")
    print(f"   - 自动登录: {status['auto_login_enabled']}")
    print(f"   - 保存账号: {status['account']}")
    print(f"   - 有凭据: {status['has_credentials']}")
    print(f"   - 需要登录: {status['should_auto_login']}")
    
    print("\n🔧 步骤3: 模拟自动登录")
    print("-" * 40)
    
    # 获取凭据
    credentials = manager.get_login_credentials()
    if credentials:
        print(f"✅ 获取到凭据: {credentials['account']}")
        print("模拟使用凭据登录...")
        
        # 更新登录日期
        manager.update_last_login_date()
        print("✅ 登录成功，已更新登录日期")
    else:
        print("❌ 没有可用的凭据")
    
    print("\n📋 登录后的状态:")
    status = manager.get_status()
    print(f"   - 启用状态: {status['enabled']}")
    print(f"   - 自动登录: {status['auto_login_enabled']}")
    print(f"   - 保存账号: {status['account']}")
    print(f"   - 有凭据: {status['has_credentials']}")
    print(f"   - 需要登录: {status['should_auto_login']}")
    print(f"   - 上次登录: {status['last_login_date']}")
    
    print("\n🔧 步骤4: 禁用自动登录")
    print("-" * 40)
    
    manager.disable_auto_login()
    print("✅ 自动登录已禁用")
    
    print("\n📋 禁用后的状态:")
    status = manager.get_status()
    print(f"   - 启用状态: {status['enabled']}")
    print(f"   - 自动登录: {status['auto_login_enabled']}")
    print(f"   - 保存账号: {status['account']}")
    print(f"   - 有凭据: {status['has_credentials']}")
    print(f"   - 需要登录: {status['should_auto_login']}")
    
    print("\n🔧 步骤5: 清除凭据")
    print("-" * 40)
    
    manager.clear_credentials()
    print("✅ 凭据已清除")
    
    print("\n📋 清除后的状态:")
    status = manager.get_status()
    print(f"   - 启用状态: {status['enabled']}")
    print(f"   - 自动登录: {status['auto_login_enabled']}")
    print(f"   - 保存账号: {status['account']}")
    print(f"   - 有凭据: {status['has_credentials']}")
    print(f"   - 需要登录: {status['should_auto_login']}")
    
    print("\n🎉 演示完成！")
    print("\n📝 使用说明:")
    print("1. 用户需要手动设置自动登录凭据")
    print("2. 设置凭据后可以启用自动登录功能")
    print("3. 系统会每天自动登录一次")
    print("4. 可以随时禁用或清除凭据")
    print("5. 所有操作都有状态反馈")

def show_config_file():
    """显示配置文件内容"""
    print("\n📄 配置文件内容:")
    print("-" * 40)
    
    try:
        with open("auto_login_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            print(json.dumps(config, indent=2, ensure_ascii=False))
    except FileNotFoundError:
        print("配置文件不存在")
    except Exception as e:
        print(f"读取配置文件失败: {e}")

if __name__ == "__main__":
    demo_auto_login_system()
    show_config_file() 