import pytest
import json
import os
from unittest import mock

@pytest.fixture
def mock_mongodb_connection():
    """模拟MongoDB连接"""
    with mock.patch('common.mongodb_client.MongoDBConnection') as mock_mongo:
        mock_instance = mock_mongo.return_value
        # 设置默认返回值
        mock_instance.connect.return_value = True
        mock_instance.find.return_value = []
        mock_instance.insert_one.return_value = 'test_id'
        mock_instance.update_one.return_value = True
        mock_instance.insert_many.return_value = ['id1', 'id2']
        yield mock_instance

@pytest.fixture
def mock_rabbitmq_connection():
    """模拟RabbitMQ连接"""
    with mock.patch('common.rabbitmq_client.RabbitMQConnection') as mock_rabbit:
        mock_instance = mock_rabbit.return_value
        # 设置默认返回值
        mock_instance.connect.return_value = True
        mock_instance.declare_exchange.return_value = True
        mock_instance.declare_queue.return_value = True
        mock_instance.bind_queue.return_value = True
        mock_instance.publish_message.return_value = True
        yield mock_instance

@pytest.fixture
def mock_logger_config():
    """模拟日志配置"""
    with mock.patch('common.logger_config.LoggerConfig') as mock_logger:
        mock_instance = mock_logger.setup_logger.return_value
        mock_instance.info = mock.MagicMock()
        mock_instance.error = mock.MagicMock()
        mock_instance.warning = mock.MagicMock()
        yield mock_instance

@pytest.fixture
def sample_config():
    """提供测试用的配置数据"""
    return {
        'mongodb': {
            'host': 'localhost',
            'port': 27017,
            'username': '',
            'password': '',
            'db_name': 'spider_db'
        },
        'rabbitmq': {
            'host': 'localhost',
            'port': 5672,
            'username': 'guest',
            'password': 'guest',
            'virtual_host': '/'
        },
        'master': {
            'task_queue': 'spider_tasks',
            'exchange_name': 'spider_exchange',
            'routing_key': 'task',
            'task_batch_size': 100,
            'polling_interval': 5
        },
        'worker': {
            'task_queue': 'spider_tasks',
            'result_exchange': 'spider_exchange',
            'result_routing_key': 'result',
            'prefetch_count': 5,
            'timeout': 300
        },
        'processor': {
            'result_queue': 'spider_results',
            'exchange_name': 'spider_exchange',
            'routing_key': 'result',
            'collection_name': 'spider_results',
            'batch_size': 50
        }
    }

@pytest.fixture
def sample_task():
    """提供测试用的任务数据"""
    return {
        '_id': 'task_123',
        'name': 'test_task',
        'status': 'pending',
        'request_params': {
            'api_url': 'https://example.com/api',
            'data': {'key': 'value'}
        },
        'need_headers': True
    }

@pytest.fixture
def sample_result():
    """提供测试用的爬取结果数据"""
    return {
        'task_id': 'task_123',
        'worker_id': 'worker_1',
        'timestamp': 1623456789.0,
        'success': True,
        'data': {'result': 'test_data'},
        'response_time': 0.5
    }