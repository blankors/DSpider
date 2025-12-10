'''
# Playwright 浏览器复用性能分析

## 为什么复用浏览器有助于性能提升？

Playwright 复用浏览器实例而不是每次访问 URL 都新建浏览器，确实能显著提升性能，主要原因如下：

### 1. 减少浏览器启动开销
- 浏览器启动需要加载大量资源（如二进制文件、扩展、配置等）
- 每次新建浏览器都会重复这个耗时的初始化过程
- 复用浏览器避免了多次启动的时间和资源消耗

### 2. 减少内存占用
- 每个浏览器实例都需要独立的内存空间
- 复用单个浏览器实例可以共享内存资源
- 减少内存分配和垃圾回收的频率

### 3. 降低 CPU 使用率
- 浏览器启动是 CPU 密集型操作
- 复用浏览器减少了 CPU 在初始化过程中的消耗
- 降低了系统上下文切换的频率

### 4. 加速页面加载
- 复用浏览器可以保留缓存（DNS、HTTP、资源缓存等）
- 避免重复建立 TCP 连接
- 可以保留某些会话状态，减少重新加载资源的时间

### 5. 提高测试/爬虫吞吐量
- 对于需要处理多个 URL 的场景（如爬虫、自动化测试）
- 复用浏览器可以显著提高任务完成速度
- 减少了整体执行时间

## 性能测试脚本

以下是一个测试脚本，用于比较复用浏览器和每次新建浏览器的性能差异：

'''
import asyncio
import time
import psutil
import playwright.async_api as playwright
import statistics

# 测试配置
TEST_URLS = [
    "https://www.baidu.com",
    "https://www.bing.com",
    "https://www.zhihu.com",
    "https://www.163.com",
    "https://www.sina.com.cn",
    "https://www.qq.com",
    "https://www.taobao.com",
    "https://www.jd.com",
    "https://www.douban.com",
    "https://www.csdn.net"
]  # 增加测试URL数量，从5个增加到10个
TEST_RUNS = 5  # 增加测试次数，从3次增加到5次
TIMEOUT = 40000  # 保持超时时间不变
RETRY_COUNT = 1  # 保持重试次数不变

class PerformanceTest:
    def __init__(self):
        self.results = {
            "reuse_browser": [],
            "new_browser_each_time": []
        }
    
    async def measure_memory_usage(self):
        """测量当前进程的内存使用情况"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    
    async def measure_cpu_usage(self, duration=0.1):
        """测量CPU使用率"""
        process = psutil.Process()
        # 先调用一次获取初始值
        process.cpu_percent()
        # 等待一段时间
        await asyncio.sleep(duration)
        # 再次调用获取使用率
        cpu_percent = process.cpu_percent()
        return cpu_percent
    
    async def test_reuse_browser(self):
        """测试复用浏览器的性能"""
        print("测试：复用浏览器")
        page_load_times = []
        test_start_time = time.time()  # 记录测试开始时间（创建playwright之前）
        start_memory = await self.measure_memory_usage()
        start_cpu = await self.measure_cpu_usage()
        
        # 移除全局的playwright_start_time，改为为每个URL单独测量
        
        async with playwright.async_playwright() as p:
            # 记录playwright创建完成的时间
            playwright_created_time = time.time()
            
            # 测量浏览器启动时间
            browser_launch_start = time.time()
            browser = await p.chromium.launch(headless=True)
            browser_start_time = time.time() - browser_launch_start
            
            # 预热阶段：创建并关闭一个页面
            warmup_page = await browser.new_page()
            await warmup_page.goto("https://www.baidu.com", timeout=TIMEOUT)
            await warmup_page.close()
            
            page_create_times = []
            url_to_newpage_times = []  # 新增列表：用于存储从处理URL到new_page完成的时间
            
            for url in TEST_URLS:
                # 记录开始处理当前URL的时间（时间a）
                url_processing_start_time = time.time()
                # 测量页面创建时间
                page_create_start = time.time()
                page = await browser.new_page()
                page_create_time = time.time() - page_create_start
                page_create_times.append(page_create_time)
                
                # 计算从开始处理URL到new_page完成的时间（时间b - 时间a）
                url_to_newpage_time = time.time() - url_processing_start_time
                url_to_newpage_times.append(url_to_newpage_time)
                      
                retry = 0
                page_load_time = None
                
                while retry <= RETRY_COUNT and page_load_time is None:
                    page_start_time = time.time()
                    try:
                        await page.goto(url, timeout=TIMEOUT)
                        page_load_time = time.time() - page_start_time
                        page_load_times.append(page_load_time)
                        print(f"成功访问 {url}，加载时间: {page_load_time:.2f} 秒")
                    except Exception as e:
                        retry += 1
                        if retry > RETRY_COUNT:
                            print(f"访问 {url} 失败 (重试 {RETRY_COUNT} 次): {e}")
                            page_load_times.append(float('inf'))  # 记录为无限大，表示失败
                        else:
                            print(f"访问 {url} 失败，正在重试 ({retry}/{RETRY_COUNT}): {e}")
                            await page.reload()
                
                await page.close()
            
            await browser.close()
            
            end_time = time.time()
            end_memory = await self.measure_memory_usage()
            end_cpu = await self.measure_cpu_usage()
            
            # 过滤掉超时的页面加载时间
            valid_page_load_times = [t for t in page_load_times if t != float('inf')]
            
            # 计算有效页面加载时间的统计数据
            avg_page_load_time = statistics.mean(valid_page_load_times) if valid_page_load_times else float('inf')
            min_page_load_time = min(valid_page_load_times) if valid_page_load_times else float('inf')
            max_page_load_time = max(valid_page_load_times) if valid_page_load_times else float('inf')
            
            result = {
                "total_time": end_time - test_start_time,
                "memory_used": end_memory - start_memory,
                "cpu_usage": end_cpu - start_cpu,
                "avg_page_load_time": avg_page_load_time,
                "min_page_load_time": min_page_load_time,
                "max_page_load_time": max_page_load_time,
                "page_load_times": page_load_times,
                "valid_page_count": len(valid_page_load_times),
                "total_page_count": len(page_load_times),
                "browser_start_time": browser_start_time,
                "avg_page_create_time": statistics.mean(page_create_times) if page_create_times else 0,
                "avg_url_to_newpage_time": statistics.mean(url_to_newpage_times) if url_to_newpage_times else 0
            }
            
            self.results["reuse_browser"].append(result)
            return result
    
    async def test_new_browser_each_time(self):
        """测试每次新建浏览器的性能"""
        print("测试：每次新建浏览器")
        
        # 移除全局的playwright_start_time，改为为每个URL单独测量
        # 记录测试开始时间（在创建playwright之前）
        test_start_time = time.time()
        
        async with playwright.async_playwright() as p:
            # 记录playwright创建完成的时间
            playwright_created_time = time.time()
            
            start_memory = await self.measure_memory_usage()
            start_cpu = await self.measure_cpu_usage()
            
            page_load_times = []
            browser_start_times = []
            page_create_times = []
            url_to_newpage_times = []  # 新增列表：用于存储从处理URL到new_page完成的时间
            
            for url in TEST_URLS:
                # 记录开始处理当前URL的时间（时间a）
                url_processing_start_time = time.time()
                # 测量浏览器启动时间
                browser_launch_start = time.time()
                browser = await p.chromium.launch(headless=True)
                browser_start_times.append(time.time() - browser_launch_start)
                
                # 测量页面创建时间
                page_create_start = time.time()
                page = await browser.new_page()
                page_create_time = time.time() - page_create_start
                page_create_times.append(page_create_time)
                
                # 计算从开始处理URL到new_page完成的时间（时间b - 时间a）
                url_to_newpage_time = time.time() - url_processing_start_time
                url_to_newpage_times.append(url_to_newpage_time)
                
                retry = 0
                page_load_time = None
                
                while retry <= RETRY_COUNT and page_load_time is None:
                    page_start_time = time.time()
                    try:
                        await page.goto(url, timeout=TIMEOUT)
                        page_load_time = time.time() - page_start_time
                        page_load_times.append(page_load_time)
                        print(f"成功访问 {url}，加载时间: {page_load_time:.2f} 秒")
                    except Exception as e:
                        retry += 1
                        if retry > RETRY_COUNT:
                            print(f"访问 {url} 失败 (重试 {RETRY_COUNT} 次): {e}")
                            page_load_times.append(float('inf'))  # 记录为无限大，表示失败
                        else:
                            print(f"访问 {url} 失败，正在重试 ({retry}/{RETRY_COUNT}): {e}")
                            await page.reload()
                
                await page.close()
                await browser.close()
            
            end_time = time.time()
            end_memory = await self.measure_memory_usage()
            end_cpu = await self.measure_cpu_usage()
            
            # 过滤掉超时的页面加载时间
            valid_page_load_times = [t for t in page_load_times if t != float('inf')]
            
            result = {
                "total_time": end_time - test_start_time,
                "memory_used": end_memory - start_memory,
                "cpu_usage": end_cpu - start_cpu,
                "avg_page_load_time": statistics.mean(valid_page_load_times) if valid_page_load_times else float('inf'),
                "min_page_load_time": min(valid_page_load_times) if valid_page_load_times else float('inf'),
                "max_page_load_time": max(valid_page_load_times) if valid_page_load_times else float('inf'),
                "page_load_times": page_load_times,
                "valid_page_count": len(valid_page_load_times),
                "total_page_count": len(page_load_times),
                "total_browser_start_time": sum(browser_start_times),
                "avg_browser_start_time": statistics.mean(browser_start_times) if browser_start_times else 0,
                "avg_page_create_time": statistics.mean(page_create_times) if page_create_times else 0,
                "avg_url_to_newpage_time": statistics.mean(url_to_newpage_times) if url_to_newpage_times else 0
            }
            
            self.results["new_browser_each_time"].append(result)
            return result
    
    def print_results(self):
        """打印测试结果"""
        print("\n" + "="*50)
        print("性能测试结果汇总")
        print("="*50)
        
        for test_type, results in self.results.items():
            print(f"\n{test_type}:")
            print("-"*30)
            
            # 计算平均值
            avg_total_time = statistics.mean(r["total_time"] for r in results)
            avg_memory_used = statistics.mean(r["memory_used"] for r in results)
            avg_cpu_usage = statistics.mean(r["cpu_usage"] for r in results)
            avg_page_load = statistics.mean(r["avg_page_load_time"] for r in results)
            
            print(f"平均总执行时间: {avg_total_time:.3f} 秒")
            print(f"平均内存使用增加: {avg_memory_used:.3f} MB")
            print(f"平均CPU使用率增加: {avg_cpu_usage:.3f} %")
            print(f"平均页面加载时间: {'{:.3f}'.format(avg_page_load) if avg_page_load != float('inf') else 'N/A'} 秒/页")
            
            # 打印浏览器和页面相关指标
            if "reuse_browser" == test_type:
                avg_browser_start = statistics.mean(r["browser_start_time"] for r in results)
                avg_page_create = statistics.mean(r["avg_page_create_time"] for r in results)
                avg_url_to_newpage = statistics.mean(r["avg_url_to_newpage_time"] for r in results)
                print(f"浏览器启动时间: {avg_browser_start:.3f} 秒")
                print(f"平均页面创建时间: {avg_page_create:.3f} 秒")
                print(f"平均从处理URL到new_page完成的时间: {avg_url_to_newpage:.3f} 秒")
            elif "new_browser_each_time" == test_type:
                avg_total_browser_start = statistics.mean(r["total_browser_start_time"] for r in results)
                avg_per_browser_start = statistics.mean(r["avg_browser_start_time"] for r in results)
                avg_page_create = statistics.mean(r["avg_page_create_time"] for r in results)
                avg_url_to_newpage = statistics.mean(r["avg_url_to_newpage_time"] for r in results)
                print(f"总浏览器启动时间: {avg_total_browser_start:.3f} 秒")
                print(f"平均每次浏览器启动时间: {avg_per_browser_start:.3f} 秒")
                print(f"平均页面创建时间: {avg_page_create:.3f} 秒")
                print(f"平均从处理URL到new_page完成的时间: {avg_url_to_newpage:.3f} 秒")
            
            # 计算成功率
            total_pages = sum(r["total_page_count"] for r in results)
            valid_pages = sum(r["valid_page_count"] for r in results)
            success_rate = (valid_pages / total_pages) * 100 if total_pages > 0 else 0
            print(f"页面访问成功率: {success_rate:.1f}%")
        
        # 计算性能提升比例
        reuse_avg = statistics.mean(r["total_time"] for r in self.results["reuse_browser"])
        new_avg = statistics.mean(r["total_time"] for r in self.results["new_browser_each_time"])
        improvement = ((new_avg - reuse_avg) / new_avg) * 100
        
        print(f"\n性能提升: {improvement:.1f}%")
        
        # 计算浏览器启动时间的差异
        if "reuse_browser" in self.results and "new_browser_each_time" in self.results:
            reuse_browser_start = statistics.mean(r["browser_start_time"] for r in self.results["reuse_browser"])
            new_browser_total_start = statistics.mean(r["total_browser_start_time"] for r in self.results["new_browser_each_time"])
            browser_start_saving = new_browser_total_start - reuse_browser_start
            print(f"浏览器启动时间节省: {browser_start_saving:.3f} 秒")
        
        print("="*50)

async def main():
    test = PerformanceTest()
    
    # 运行多次测试以获得更准确的结果
    for i in range(TEST_RUNS):
        print(f"\n第 {i+1}/{TEST_RUNS} 次测试")
        await test.test_reuse_browser()
        await test.test_new_browser_each_time()
    
    test.print_results()

if __name__ == "__main__":
    asyncio.run(main())
