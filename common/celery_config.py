from celery import Celery
import os
import sys
import platform
from common.load_config import config

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 创建 Celery 实例
celery_app = Celery('DSpider')

# 基础配置
celery_config = {
    'broker_url': f"amqp://{config['rabbitmq']['username']}:{config['rabbitmq']['password']}@{config['rabbitmq']['host']}:{config['rabbitmq']['port']}/{config['rabbitmq']['virtual_host']}",
    'result_backend': 'rpc://',
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'Asia/Shanghai',
    'enable_utc': True,
    'task_acks_late': True,
    'worker_prefetch_multiplier': 1,
}

# Windows特定配置
if platform.system() == 'Windows':
    celery_config.update({
        'worker_pool': 'solo',  # Windows不支持prefork池
        'worker_hijack_root_logger': False,
        'worker_redirect_stdouts': False,
    })

# 配置 Celery
celery_app.conf.update(celery_config)

# 自动发现任务
# 修改任务发现路径以支持本地和Docker环境
celery_app.autodiscover_tasks(['worker'])
