import asyncio
import time
import platform
from dspider.celery_worker.tasks import CookieBrowser

async def test_process_url(browser_instance, url, api_url):
    """模拟单个URL处理"""
    browser_instance.set_datasource_config({
        'url': url,
        'request_params': {'api_url': api_url}
    })
    
    # 模拟process_url方法的关键部分
    if not browser_instance.browser:
        print(f"[Loop {id(asyncio.get_event_loop())}] Initializing browser...")
        await browser_instance.initialize()
    
    print(f"[Loop {id(asyncio.get_event_loop())}] Creating new page...")
    page = await browser_instance.browser.new_page()  # 这里会触发错误
    
    try:
        # 模拟页面操作
        await asyncio.sleep(1)
        return {'url': url, 'success': True}
    finally:
        await page.close()

def simulate_celery_task(browser_instance, task_id):
    """模拟Celery任务的事件循环管理"""
    print(f"\n=== Task {task_id} starting ===")
    
    # 模拟Celery任务的事件循环处理逻辑
    if platform.system() == 'Windows':
        try:
            old_loop = asyncio.get_event_loop()
            if not old_loop.is_closed():
                print(f"[Task {task_id}] Closing old loop {id(old_loop)}...")
                old_loop.close()
        except RuntimeError:
            pass
    
    # 创建新的事件循环
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    print(f"[Task {task_id}] Created new loop {id(new_loop)}")
    
    try:
        # 执行异步操作
        result = new_loop.run_until_complete(
            test_process_url(browser_instance, 
                           f"https://example.com/task{task_id}",
                           f"https://api.example.com/task{task_id}")
        )
        print(f"[Task {task_id}] Result: {result}")
        return result
    except Exception as e:
        print(f"[Task {task_id}] ERROR: {type(e).__name__}: {e}")
        return {'error': str(e)}
    finally:
        # 关闭事件循环
        print(f"[Task {task_id}] Closing loop {id(new_loop)}...")
        new_loop.close()

if __name__ == "__main__":
    print("=== Reproducing event loop error ===")
    print("Creating global CookieBrowser instance...")
    
    # 创建全局CookieBrowser实例（问题的根源）
    global_browser = CookieBrowser()
    
    # 模拟多个Celery任务执行
    for i in range(3):
        simulate_celery_task(global_browser, i+1)
        time.sleep(1)
    
    print("\n=== Test completed ===")