#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署测试脚本
用于验证部署是否成功
"""

import requests
import json
import time
import sys
import os

def test_health_check(base_url):
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data.get('status', 'unknown')}")
            print(f"   版本: {data.get('version', 'unknown')}")
            print(f"   时间: {data.get('timestamp', 'unknown')}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_login_page(base_url):
    """测试登录页面"""
    print("\n🔍 测试登录页面...")
    try:
        response = requests.get(f"{base_url}/login", timeout=10)
        if response.status_code == 200:
            print("✅ 登录页面访问正常")
            return True
        else:
            print(f"❌ 登录页面访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 登录页面异常: {e}")
        return False

def test_api_endpoints(base_url):
    """测试API接口"""
    print("\n🔍 测试API接口...")
    
    # 测试任务状态API
    try:
        response = requests.get(f"{base_url}/api/task_status", timeout=10)
        if response.status_code == 200:
            print("✅ 任务状态API正常")
        else:
            print(f"❌ 任务状态API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 任务状态API异常: {e}")
    
    # 测试代理状态API
    try:
        response = requests.get(f"{base_url}/api/proxy_status", timeout=10)
        if response.status_code == 200:
            print("✅ 代理状态API正常")
        else:
            print(f"❌ 代理状态API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 代理状态API异常: {e}")
    
    # 测试自动登录状态API
    try:
        response = requests.get(f"{base_url}/api/auto_login_status", timeout=10)
        if response.status_code == 200:
            print("✅ 自动登录状态API正常")
        else:
            print(f"❌ 自动登录状态API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 自动登录状态API异常: {e}")

def test_ssl_certificate(base_url):
    """测试SSL证书"""
    print("\n🔍 测试SSL证书...")
    try:
        response = requests.get(base_url, timeout=10, verify=True)
        if response.status_code in [200, 301, 302]:
            print("✅ SSL证书验证通过")
            return True
        else:
            print(f"❌ SSL证书验证失败: {response.status_code}")
            return False
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL证书错误: {e}")
        return False
    except Exception as e:
        print(f"❌ SSL测试异常: {e}")
        return False

def test_performance(base_url):
    """测试性能"""
    print("\n🔍 测试性能...")
    
    # 测试响应时间
    times = []
    for i in range(5):
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}/health", timeout=10)
            end_time = time.time()
            if response.status_code == 200:
                times.append(end_time - start_time)
        except Exception as e:
            print(f"❌ 性能测试异常: {e}")
            break
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"✅ 平均响应时间: {avg_time:.3f}秒")
        if avg_time < 1.0:
            print("✅ 性能良好")
        elif avg_time < 3.0:
            print("⚠️  性能一般")
        else:
            print("❌ 性能较差")
    else:
        print("❌ 性能测试失败")

def test_docker_services():
    """测试Docker服务"""
    print("\n🔍 测试Docker服务...")
    
    try:
        import subprocess
        
        # 检查容器状态
        result = subprocess.run(['docker-compose', 'ps'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Docker Compose服务正常")
            print(result.stdout)
        else:
            print("❌ Docker Compose服务异常")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Docker服务测试异常: {e}")

def main():
    """主函数"""
    print("🚀 IBOX管理系统部署测试")
    print("=" * 50)
    
    # 获取测试URL
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost"
    
    print(f"测试地址: {base_url}")
    
    # 运行测试
    tests = [
        ("健康检查", lambda: test_health_check(base_url)),
        ("登录页面", lambda: test_login_page(base_url)),
        ("API接口", lambda: test_api_endpoints(base_url)),
        ("SSL证书", lambda: test_ssl_certificate(base_url)),
        ("性能测试", lambda: test_performance(base_url)),
        ("Docker服务", lambda: test_docker_services()),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！部署成功！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查部署配置")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 