# 容器环境事件循环错误复现指南

## 问题描述
在Docker容器中运行Celery worker时，使用全局CookieBrowser实例会导致以下错误：
```
Browser.new_page: The future belongs to a different loop than the one specified as the loop argument
```

## 问题根源

### 容器环境特点
1. **Linux环境**：容器使用Linux系统，Celery默认使用`prefork`进程池
2. **多进程并发**：每个worker任务在独立进程中执行
3. **事件循环生命周期**：每个任务创建新的事件循环
4. **全局实例共享**：全局CookieBrowser实例在不同进程间共享（实际是复制）

### 错误发生机制
```
1. 启动Celery worker，创建全局CookieBrowser实例
2. 任务1启动，创建事件循环Loop1
3. 任务1调用initialize()，浏览器实例绑定到Loop1
4. 任务1完成，Loop1被销毁
5. 任务2启动，创建事件循环Loop2
6. 任务2复用全局CookieBrowser实例（包含绑定到Loop1的浏览器）
7. 任务2调用browser.new_page()，尝试在Loop2中使用绑定到Loop1的浏览器
8. 抛出事件循环不匹配错误
```

## 复现方案

### 方案1：使用Docker Compose（推荐）

#### 1. 构建并运行测试容器
```bash
# 在项目根目录运行
docker-compose -f docker-compose.test.yml up --build
```

#### 2. 预期输出
```
=== Worker 0 启动 ===
Worker 0: 创建事件循环 140300000000000
Worker 0: 初始化浏览器
Worker 0: 尝试创建新页面
Worker 0: 页面创建成功
Worker 0: 任务完成

=== Worker 1 启动 ===
Worker 1: 创建事件循环 140300000000000
Worker 1: 尝试创建新页面
Worker 1: 错误 - Error: Browser.new_page: The future belongs to a different loop than the one specified as the loop argument
Worker 1: 成功复现事件循环不匹配错误！
Worker 1: 任务失败 - Browser.new_page: The future belongs to a different loop than the one specified as the loop argument
```

### 方案2：直接在Linux宿主机/容器中运行

#### 1. 运行简化复现脚本
```bash
cd /app
python -m test.simple_reproduce
```

#### 2. 运行完整复现脚本
```bash
cd /app
python -m test.container_reproduce
```

## 解决方案

### 最佳实践：任务内创建独立实例
```python
@celery_app.task(bind=True)
def process_url_task(self, data):
    # 在任务内部创建独立实例
    cookie_browser = CookieBrowser()
    cookie_browser.set_datasource_config(data)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(cookie_browser.process_url())
        return result
    finally:
        # 确保资源释放
        if loop.is_running():
            loop.run_until_complete(cookie_browser.close())
        loop.close()
```

### 解决方案优势
1. **事件循环匹配**：每个实例绑定到任务自己的事件循环
2. **资源隔离**：每个任务独立管理浏览器资源
3. **稳定性**：避免跨进程/跨循环的资源冲突
4. **可扩展性**：支持高并发场景

## 环境差异分析

### Windows宿主机
- 默认使用`celery pool=solo`（单进程）
- 事件循环生命周期与进程绑定
- 难以复现多进程环境下的问题

### Docker容器
- 默认使用`celery pool=prefork`（多进程）
- 每个任务创建新进程和事件循环
- 全局实例在不同进程间的复制导致事件循环冲突

## 测试环境清理

```bash
# 停止并删除测试容器
docker-compose -f docker-compose.test.yml down

# 删除测试镜像
docker rmi dspider-reproduce_test
```

## 结论

容器环境中出现事件循环错误的根本原因是：
- 全局CookieBrowser实例与动态创建的事件循环生命周期不匹配
- 多进程环境下，每个任务的事件循环是独立的
- 浏览器实例绑定到特定事件循环，无法在其他循环中使用

最可靠的解决方案是在每个任务内部创建独立的CookieBrowser实例，并在任务结束时正确清理资源。