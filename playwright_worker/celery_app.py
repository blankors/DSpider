import sys
import os

from celery import Celery

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright_worker.celery_config import celery_config


# 创建 Celery 实例
celery_app = Celery('DSpider')
# 配置 Celery
celery_app.conf.update(celery_config)

# 自动发现任务
celery_app.autodiscover_tasks(['playwright_worker'])

# 在文件末尾导入任务模块，确保任务被注册，避免循环导入
import playwright_worker.worker