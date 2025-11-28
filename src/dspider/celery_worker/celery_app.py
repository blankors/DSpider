import sys
import os

from celery import Celery

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dspider.celery_worker.celery_config import celery_config

# 创建 Celery 实例
celery_app = Celery('DSpider')
celery_app.conf.update(celery_config)

# 自动发现任务
celery_app.autodiscover_tasks(['dspider.celery_worker'], related_name='tasks')
