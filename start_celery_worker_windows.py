#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows环境下启动Celery worker的脚本
"""
import os
import sys
import subprocess
import platform
import time

# 检查是否在Windows环境下运行
if platform.system() != 'Windows':
    print("这个脚本仅在Windows环境下运行")
    sys.exit(1)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量以避免权限问题
os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = '1'

def start_celery_worker():
    """启动Celery worker"""
    print("在Windows环境下启动Celery worker...")
    
    # 构建Celery worker启动命令
    command = [
        'celery',
        '-A', 'common.celery_config',
        'worker',
        '--loglevel=info',
        '--pool=solo',  # Windows必须使用solo池
        '--concurrency=1',  # Windows下使用1个并发
        '--without-gossip',  # 减少网络流量
        '--without-mingle',  # 启动时不进行节点握手
        '--without-heartbeat',  # 禁用心跳（Windows下有时会有问题）
    ]
    
    print(f"执行命令: {' '.join(command)}")
    
    try:
        # 执行命令
        subprocess.run(command, check=True)
    except KeyboardInterrupt:
        print("\n用户中断，正在停止...")
    except subprocess.CalledProcessError as e:
        print(f"Celery worker启动失败: {e}")
        sys.exit(1)

def start_worker_script():
    """启动worker.py脚本"""
    print("启动worker.py脚本...")
    
    worker_script = os.path.join('worker', 'worker.py')
    
    if not os.path.exists(worker_script):
        print(f"worker.py文件不存在: {worker_script}")
        return False
    
    command = [sys.executable, worker_script]
    print(f"执行命令: {' '.join(command)}")
    
    try:
        # 执行命令
        subprocess.run(command, check=True)
    except KeyboardInterrupt:
        print("\n用户中断，正在停止...")
    except subprocess.CalledProcessError as e:
        print(f"worker.py启动失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("DSpider Windows启动助手")
    print("=" * 60)
    print("1. 启动Celery worker")
    print("2. 启动worker.py脚本")
    print("3. 退出")
    print("=" * 60)
    
    choice = input("请选择要执行的操作 (1-3): ")
    
    if choice == '1':
        start_celery_worker()
    elif choice == '2':
        start_worker_script()
    elif choice == '3':
        print("再见！")
    else:
        print("无效的选择，请重新运行脚本并选择1-3之间的数字")

if __name__ == '__main__':
    main()
