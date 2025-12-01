import os
import sys
import platform
from dspider.common.load_config import config

# 基础配置
celery_config = {
    'broker_url': f"amqp://{config['rabbitmq']['username']}:{config['rabbitmq']['password']}@{config['rabbitmq']['host']}:{config['rabbitmq']['port']}/{config['rabbitmq']['virtual_host']}",
    'result_backend': f"mongodb://{config['mongodb']['username']}:{config['mongodb']['password']}@{config['mongodb']['host']}:{config['mongodb']['port']}/{config['mongodb']['db_name']}?authSource=admin",
    'result_backend_transport_options': {
        'collection': 'cookies',
    },
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


