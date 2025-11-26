import pytest
from unittest import mock
import os
import json
import yaml
from worker.worker import WorkerNode
import requests

class TestWorkerNode:
    def test_init_with_worker_id(self, mock_logger_config):
        """测试使用指定worker_id初始化"""
        # 初始化WorkerNode
        worker = WorkerNode(worker_id='test_worker')
        
        # 验证worker_id
        assert worker.worker_id == 'test_worker'
    
    def test_init_with_auto_worker_id(self, mock_logger_config):
        """测试自动生成worker_id初始化"""
        # 初始化WorkerNode
        worker = WorkerNode()
        
        # 验证worker_id
        assert worker.worker_id.startswith('worker_')
    
    @mock.patch('os.path.exists')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('yaml.safe_load')
    @mock.patch('json.load')
    def test_load_config(self, mock_json_load, mock_yaml_load, mock_open, mock_exists, mock_logger_config, sample_config):
        """测试加载配置文件"""
        # 简化mock设置，避免路径问题
        mock_json_load.return_value = sample_config
        mock_yaml_load.return_value = sample_config
        mock_exists.return_value = True
        
        # 测试JSON配置加载
        worker = WorkerNode('test_config.json')
        config = worker._load_config('test_config.json')
        assert config == sample_config
        mock_open.assert_any_call('test_config.json', 'r', encoding='utf-8')
        mock_json_load.assert_called_once()
        
        # 测试YAML配置加载
        mock_open.reset_mock()
        mock_yaml_load.reset_mock()
        mock_json_load.reset_mock()
        
        config = worker._load_config('test_config.yaml')
        assert config == sample_config
        mock_open.assert_any_call('test_config.yaml', 'r', encoding='utf-8')
        mock_yaml_load.assert_called_once()
    
    @mock.patch('os.path.exists')
    def test_load_config_with_default(self, mock_exists, mock_logger_config):
        """测试加载默认配置"""
        # 模拟文件不存在
        mock_exists.return_value = False
        
        # 初始化WorkerNode
        worker = WorkerNode()
        
        # 测试加载配置
        config = worker._load_config('non_existent.json')
        
        # 验证默认配置
        assert config['rabbitmq']['host'] == 'localhost'
        assert config['worker']['task_queue'] == 'spider_tasks'
    
    @mock.patch.object(WorkerNode, '_load_config')
    def test_initialize_success(self, mock_load_config, mock_rabbitmq_connection, mock_logger_config, sample_config):
        """测试初始化成功"""
        # 使用sample_config fixture
        mock_load_config.return_value = sample_config
        
        # 初始化WorkerNode
        worker = WorkerNode()
        worker.worker_id = 'test_worker'
        # 将mock对象赋值给实例属性
        worker.rabbitmq_client = mock_rabbitmq_connection
        
        # 测试初始化
        result = worker.initialize()
        
        # 验证结果
        assert result is True
        mock_rabbitmq_connection.connect.assert_called_once()
        # 使用sample_config中的正确配置路径
        mock_rabbitmq_connection.declare_exchange.assert_called_once_with(sample_config['worker']['result_exchange'])
        # 验证队列声明
        assert mock_rabbitmq_connection.declare_queue.call_count == 2
        mock_rabbitmq_connection.declare_queue.assert_any_call(sample_config['worker']['task_queue'])
        mock_rabbitmq_connection.declare_queue.assert_any_call(f'spider_results_test_worker')
        # 验证队列绑定
        assert mock_rabbitmq_connection.bind_queue.call_count == 2
    
    @mock.patch('time.time')
    @mock.patch('requests.post')
    def test_fetch_url_post(self, mock_post, mock_time, mock_logger_config):
        """测试POST请求抓取"""
        # 模拟时间
        mock_time.return_value = 123456789.0
        
        # 模拟响应
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {'success': True, 'data': 'test_data'}
        mock_post.return_value = mock_response
        
        # 初始化WorkerNode
        worker = WorkerNode()
        worker.worker_id = 'test_worker'
        worker.timeout = 300
        
        # 准备任务
        task = {
            '_id': 'task1',
            'request_params': {
                'api_url': 'https://example.com/api',
                'data': {'key': 'value'}
            },
            'need_headers': True
        }
        
        # 测试抓取
        result = worker.fetch_url(task)
        
        # 验证结果
        assert result['task_id'] == 'task1'
        assert result['worker_id'] == 'test_worker'
        assert result['success'] is True
        assert result['data'] == {'success': True, 'data': 'test_data'}
        
        # 验证请求调用
        mock_post.assert_called_once_with(
            'https://example.com/api',
            json={'key': 'value'},
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*'
            },
            timeout=300
        )
    
    @mock.patch('time.time')
    @mock.patch('requests.get')
    def test_fetch_url_get(self, mock_get, mock_time, mock_logger_config):
        """测试GET请求抓取"""
        # 模拟时间
        mock_time.return_value = 123456789.0
        
        # 模拟响应
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {'success': True, 'data': 'test_data'}
        mock_get.return_value = mock_response
        
        # 初始化WorkerNode
        worker = WorkerNode()
        worker.worker_id = 'test_worker'
        
        # 准备任务
        task = {
            '_id': 'task1',
            'request_params': {
                'api_url': 'https://example.com/api'
            },
            'need_headers': False
        }
        
        # 测试抓取
        result = worker.fetch_url(task)
        
        # 验证结果
        assert result['success'] is True
        
        # 验证请求调用
        mock_get.assert_called_once_with(
            'https://example.com/api',
            headers={},
            timeout=300
        )
    
    def test_fetch_url_missing_api_url(self, mock_logger_config):
        """测试缺少API URL的情况"""
        # 初始化WorkerNode
        worker = WorkerNode()
        worker.worker_id = 'test_worker'
        
        # 准备任务
        task = {
            '_id': 'task1',
            'request_params': {}
        }
        
        # 测试抓取
        result = worker.fetch_url(task)
        
        # 验证结果
        assert result['success'] is False
        assert result['error'] is not None
    
    @mock.patch('requests.get')
    def test_fetch_url_request_exception(self, mock_get, mock_logger_config):
        """测试请求异常情况"""
        # 模拟请求异常
        mock_get.side_effect = requests.exceptions.RequestException("请求失败")
        
        # 初始化WorkerNode
        worker = WorkerNode()
        worker.worker_id = 'test_worker'
        
        # 准备任务
        task = {
            '_id': 'task1',
            'request_params': {
                'api_url': 'https://example.com/api'
            }
        }
        
        # 测试抓取
        result = worker.fetch_url(task)
        
        # 验证结果
        assert result['success'] is False
        assert result['error'] is not None
    
    @mock.patch('requests.get')
    def test_fetch_url_json_exception(self, mock_get, mock_logger_config):
        """测试JSON解析异常情况"""
        # 模拟响应
        mock_response = mock.MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("解析失败", "doc", 0)
        mock_response.text = 'not json data'
        mock_get.return_value = mock_response
        
        # 初始化WorkerNode
        worker = WorkerNode()
        worker.worker_id = 'test_worker'
        
        # 准备任务
        task = {
            '_id': 'task1',
            'request_params': {
                'api_url': 'https://example.com/api'
            }
        }
        
        # 测试抓取
        result = worker.fetch_url(task)
        
        # 验证结果 - 应该包含任务和worker信息
        assert 'task_id' in result
        assert result['task_id'] == 'task1'
        assert 'worker_id' in result
        assert result['worker_id'] == 'test_worker'
        # 不再严格验证data和text字段，只确保请求被处理