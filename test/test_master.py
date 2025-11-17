import pytest
from unittest import mock
import os
import json
from master.master import MasterNode

class TestMasterNode:
    @mock.patch('os.path.exists')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('json.load')
    def test_init_with_config(self, mock_json_load, mock_open, mock_exists, mock_logger_config, sample_config):
        """测试使用配置文件初始化"""
        # 简化mock设置，避免路径问题
        mock_json_load.return_value = sample_config
        mock_exists.return_value = True

        # 初始化MasterNode
        master = MasterNode('test_config.json')

        # 验证配置加载
        assert master.config == sample_config
        # 只验证配置文件被调用，不限制调用次数
        mock_open.assert_any_call('test_config.json', 'r', encoding='utf-8')
    
    @mock.patch('os.path.exists')
    def test_init_with_default_config(self, mock_exists, mock_logger_config):
        """测试使用默认配置初始化"""
        # 模拟文件不存在
        mock_exists.return_value = False
        
        # 初始化MasterNode
        master = MasterNode('non_existent.json')
        
        # 验证默认配置
        assert master.config['mongodb']['host'] == 'localhost'
        assert master.config['rabbitmq']['host'] == 'localhost'
    
    @mock.patch.object(MasterNode, '_load_config')
    def test_initialize_success(self, mock_load_config, mock_mongodb_connection, mock_rabbitmq_connection, mock_logger_config, sample_config):
        """测试初始化成功"""
        # 使用sample_config fixture
        mock_load_config.return_value = sample_config
        
        # 初始化MasterNode
        master = MasterNode()
        
        # 测试初始化
        result = master.initialize()
        
        # 验证初始化过程
        assert result is True
        master.mongo_client.connect.assert_called_once()
        master.rabbitmq_client.connect.assert_called_once()
        master.rabbitmq_client.declare_exchange.assert_called_once_with(sample_config['master']['exchange_name'])
        master.rabbitmq_client.declare_queue.assert_called_once_with(sample_config['master']['task_queue'])
        master.rabbitmq_client.bind_queue.assert_called_once_with(
            sample_config['master']['task_queue'], 
            sample_config['master']['exchange_name'], 
            sample_config['master']['routing_key']
        )
    
    @mock.patch.object(MasterNode, '_load_config')
    def test_initialize_mongodb_failure(self, mock_load_config, mock_mongodb_connection, mock_rabbitmq_connection, mock_logger_config, sample_config):
        """测试MongoDB连接失败的初始化"""
        # 使用sample_config fixture
        mock_load_config.return_value = sample_config
        
        # 模拟MongoDB连接失败
        mock_mongodb_connection.connect.return_value = False
        
        # 初始化MasterNode，将mock对象赋值给实例属性
        master = MasterNode()
        master.mongo_client = mock_mongodb_connection
        master.rabbitmq_client = mock_rabbitmq_connection
        
        # 测试初始化
        result = master.initialize()
        
        # 验证结果
        assert result is False
        mock_mongodb_connection.connect.assert_called_once()
        mock_rabbitmq_connection.connect.assert_not_called()
    
    def test_load_tasks_from_mongodb(self, mock_mongodb_connection, mock_logger_config):
        """测试从MongoDB加载任务"""
        # 模拟任务数据
        mock_tasks = [{'_id': 'task1', 'status': 'pending'}, {'_id': 'task2', 'status': 'pending'}]
        mock_mongodb_connection.find.return_value = mock_tasks
        
        # 初始化MasterNode
        master = MasterNode()
        master.mongo_client = mock_mongodb_connection
        master.task_batch_size = 100
        
        # 测试加载任务
        tasks = master.load_tasks_from_mongodb()
        
        # 验证结果
        assert tasks == mock_tasks
        mock_mongodb_connection.find.assert_called_once_with(
            'WebsiteConfig',
            {'status': {'$ne': 'completed'}},
            limit=100
        )
    
    def test_load_tasks_from_mongodb_exception(self, mock_mongodb_connection, mock_logger_config):
        """测试加载任务异常情况"""
        # 模拟异常
        mock_mongodb_connection.find.side_effect = Exception("查询失败")
        
        # 初始化MasterNode
        master = MasterNode()
        master.mongo_client = mock_mongodb_connection
        
        # 测试加载任务
        tasks = master.load_tasks_from_mongodb()
        
        # 验证结果
        assert tasks == []
    
    @mock.patch('time.time')
    def test_distribute_tasks(self, mock_time, mock_mongodb_connection, mock_rabbitmq_connection, mock_logger_config):
        """测试分发任务"""
        # 模拟时间
        mock_time.return_value = 123456789.0
        
        # 模拟任务
        tasks = [
            {'_id': 'task1', 'status': 'pending'},
            {'id': 'task2', 'status': 'pending'}  # 没有_id，需要使用id
        ]
        
        # 初始化MasterNode
        master = MasterNode()
        master.mongo_client = mock_mongodb_connection
        master.rabbitmq_client = mock_rabbitmq_connection
        master.exchange_name = 'test_exchange'
        master.routing_key = 'test_key'
        
        # 测试分发任务
        success_count = master.distribute_tasks(tasks)
        
        # 验证结果
        assert success_count == 2
        # 验证发布消息调用
        assert mock_rabbitmq_connection.publish_message.call_count == 2
        # 验证更新状态调用
        assert mock_mongodb_connection.update_one.call_count == 2
    
    @mock.patch.object(MasterNode, 'initialize')
    @mock.patch.object(MasterNode, 'load_tasks_from_mongodb')
    @mock.patch.object(MasterNode, 'distribute_tasks')
    @mock.patch('time.sleep')
    def test_run_normal(self, mock_sleep, mock_distribute_tasks, mock_load_tasks, mock_initialize, mock_logger_config):
        """测试正常运行流程"""
        # 模拟初始化成功
        mock_initialize.return_value = True
        # 模拟没有任务
        mock_load_tasks.return_value = []
        # 模拟sleep抛出KeyboardInterrupt来结束循环
        mock_sleep.side_effect = KeyboardInterrupt
        
        # 初始化MasterNode
        master = MasterNode()
        master.polling_interval = 5
        
        # 测试运行
        master.run()
        
        # 验证调用
        mock_initialize.assert_called_once()
        mock_load_tasks.assert_called_once()
        mock_distribute_tasks.assert_not_called()
        mock_sleep.assert_called_once_with(5)
    
    @mock.patch.object(MasterNode, 'initialize')
    @mock.patch.object(MasterNode, 'load_tasks_from_mongodb')
    @mock.patch.object(MasterNode, 'distribute_tasks')
    @mock.patch('time.sleep')
    def test_run_with_tasks(self, mock_sleep, mock_distribute_tasks, mock_load_tasks, mock_initialize, mock_logger_config):
        """测试有任务的运行流程"""
        # 模拟初始化成功
        mock_initialize.return_value = True
        # 模拟有任务
        mock_tasks = [{'_id': 'task1'}]
        mock_load_tasks.return_value = mock_tasks
        # 模拟sleep抛出KeyboardInterrupt来结束循环
        mock_sleep.side_effect = KeyboardInterrupt
        
        # 初始化MasterNode
        master = MasterNode()
        
        # 测试运行
        master.run()
        
        # 验证调用
        mock_distribute_tasks.assert_called_once_with(mock_tasks)