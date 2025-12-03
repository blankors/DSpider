import asyncio
import multiprocessing
import sys
import platform
from dspider.celery_worker.tasks import CookieBrowser

def create_global_browser():
    """创建全局CookieBrowser实例"""
    return CookieBrowser()

global_cookie_browser = create_global_browser()

def worker_process(worker_id):
    """模拟Celery worker进程"""
    print(f"\n=== Worker {worker_id} 启动 ===")
    
    # 在每个进程中创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    print(f"Worker {worker_id}: 创建事件循环 {id(loop)}")
    
    async def process_task():
        """处理单个任务"""
        # 设置配置
        global_cookie_browser.set_datasource_config({
            'url': f'https://example.com/task{worker_id}',
            'request_params': {'api_url': f'https://api.example.com/{worker_id}'}
        })
        
        try:
            # 初始化浏览器（如果尚未初始化）
            if not global_cookie_browser.browser:
                print(f"Worker {worker_id}: 初始化浏览器")
                await global_cookie_browser.initialize()
            
            # 创建新页面 - 这里会导致事件循环错误
            print(f"Worker {worker_id}: 尝试创建新页面")
            page = await global_cookie_browser.browser.new_page()
            print(f"Worker {worker_id}: 页面创建成功")
            
            # 模拟页面操作
            await asyncio.sleep(0.5)
            
            return f"Worker {worker_id}: 任务完成"
            
        except Exception as e:
            print(f"Worker {worker_id}: 错误 - {type(e).__name__}: {e}")
            if "different loop" in str(e):
                print("Worker {worker_id}: 成功复现事件循环不匹配错误！")
            return f"Worker {worker_id}: 任务失败 - {e}"
        finally:
            # 清理
            if global_cookie_browser.browser and worker_id == 0:
                # 只有第一个worker关闭浏览器
                await global_cookie_browser.close()
    
    try:
        # 运行异步任务
        result = loop.run_until_complete(process_task())
        print(result)
    finally:
        # 关闭事件循环
        loop.close()
        print(f"Worker {worker_id}: 关闭事件循环")

def main():
    """主函数"""
    print("=== 事件循环错误复现测试 ===")
    print(f"系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {sys.version}")
    print(f"进程数: {multiprocessing.cpu_count()}")
    
    # 创建多个进程模拟Celery worker
    processes = []
    num_workers = 2  # 使用2个进程足以复现问题
    
    for i in range(num_workers):
        p = multiprocessing.Process(target=worker_process, args=(i,))
        processes.append(p)
        p.start()
    
    # 等待所有进程完成
    for p in processes:
        p.join()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()