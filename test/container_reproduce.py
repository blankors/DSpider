import asyncio
import time
import threading
import multiprocessing
import sys
import platform
from dspider.celery_worker.tasks import CookieBrowser

global_cookie_browser = CookieBrowser()

async def test_process_url(url, api_url, loop_id):
    """测试处理URL，模拟实际任务"""
    global_cookie_browser.set_datasource_config({
        'url': url,
        'request_params': {'api_url': api_url}
    })
    
    # 模拟process_url方法
    if not global_cookie_browser.browser:
        print(f"[Loop {loop_id}] 初始化浏览器...")
        await global_cookie_browser.initialize()
    
    print(f"[Loop {loop_id}] 创建新页面...")
    try:
        # 这里会触发事件循环不匹配错误
        page = await global_cookie_browser.browser.new_page()
        print(f"[Loop {loop_id}] 页面创建成功")
        
        # 模拟页面操作
        await asyncio.sleep(1)
        return {'url': url, 'success': True}
    except Exception as e:
        print(f"[Loop {loop_id}] 错误: {type(e).__name__}: {e}")
        return {'error': str(e)}
    finally:
        if 'page' in locals():
            await page.close()

def run_in_new_loop(task_id):
    """在新的事件循环中运行任务"""
    print(f"\n=== 任务 {task_id} 开始 ===")
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop_id = id(loop)
    print(f"[任务 {task_id}] 创建新循环: {loop_id}")
    
    try:
        # 执行异步任务
        result = loop.run_until_complete(
            test_process_url(
                f"https://example.com/task{task_id}",
                f"https://api.example.com/task{task_id}",
                loop_id
            )
        )
        print(f"[任务 {task_id}] 结果: {result}")
    finally:
        # 关闭循环
        print(f"[任务 {task_id}] 关闭循环: {loop_id}")
        loop.close()

def simulate_multiprocess_celery():
    """模拟多进程Celery worker环境"""
    print("=== 模拟多进程Celery Worker环境 ===")
    print(f"CPU核心数: {multiprocessing.cpu_count()}")
    
    # 使用进程池模拟Celery的prefork池
    with multiprocessing.Pool(processes=2) as pool:
        # 提交多个任务
        pool.map(run_in_new_loop, range(3))

def simulate_multithread_celery():
    """模拟多线程Celery worker环境"""
    print("\n=== 模拟多线程Celery Worker环境 ===")
    
    threads = []
    for i in range(3):
        t = threading.Thread(target=run_in_new_loop, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()

def simulate_single_process_multiple_loops():
    """模拟单进程但多个事件循环的情况"""
    print("\n=== 模拟单进程多事件循环 ===")
    
    for i in range(3):
        run_in_new_loop(i)

if __name__ == "__main__":
    print("=== 开始复现事件循环错误 ===")
    print(f"Python版本: {sys.version}")
    print(f"OS: {platform.system()}")
    
    # 选择复现方式
    print("\n1. 模拟多进程环境 (Linux默认)")
    print("2. 模拟多线程环境")
    print("3. 模拟单进程多事件循环")
    
    choice = input("请选择复现方式 (1-3): ")
    
    if choice == "1":
        simulate_multiprocess_celery()
    elif choice == "2":
        simulate_multithread_celery()
    elif choice == "3":
        simulate_single_process_multiple_loops()
    else:
        print("无效选择")
        simulate_single_process_multiple_loops()
    
    print("\n=== 测试结束 ===")