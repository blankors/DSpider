import unittest
from unittest.mock import Mock
from unittest.mock import patch
import sys
import os

# from context import worker
from dspider.worker.worker import WorkerNode
from dspider.common.datasource_manager import DataSourceManager, data_source_type

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from test.test_data.data import jd_config, jd_config_tencent, jd_result_tencent, task_config

class TestWorkerNode(unittest.TestCase):
    def setUp(self):
        # 模拟数据源管理器
        self.mock_get_data_source_with_config = patch.object(DataSourceManager, 'get_data_source_with_config').start()
        self.addCleanup(patch.stopall)
        
        # 创建模拟的RabbitMQ服务
        self.mock_rabbitmq_service = Mock()
        
        # 设置数据源管理器的side_effect
        def mock_get_data_source_side_effect(data_source_type_):
            if data_source_type_ == data_source_type.RABBITMQ.value:
                return self.mock_rabbitmq_service
            else:
                return Mock()
        
        self.mock_get_data_source_with_config.side_effect = mock_get_data_source_side_effect
        
        # 创建WorkerNode实例
        self.worker_node = WorkerNode()
        
        # 模拟logger
        self.worker_node.logger = Mock()
    
    def test_run_normal_execution(self):
        """测试run方法正常执行"""
        # 执行run方法
        self.worker_node.run()
        
        # 验证consume_messages被正确调用
        self.mock_rabbitmq_service.consume_messages.assert_called_once_with(
            self.worker_node.task_queue_name,
            callback=self.worker_node.process_task,
            auto_ack=False,
            prefetch_count=self.worker_node.prefetch_count
        )
    
    def test_run_keyboard_interrupt(self):
        """测试run方法捕获KeyboardInterrupt异常"""
        # 模拟consume_messages抛出KeyboardInterrupt
        self.mock_rabbitmq_service.consume_messages.side_effect = KeyboardInterrupt()
        
        # 执行run方法
        self.worker_node.run()
        
        # 验证logger.info被调用，记录用户中断信息
        self.worker_node.logger.info.assert_called_once()
        self.assertIn("用户中断", self.worker_node.logger.info.call_args[0][0])
    
    def test_run_exception(self):
        """测试run方法捕获其他异常"""
        # 模拟consume_messages抛出异常
        test_exception = Exception("Test exception")
        self.mock_rabbitmq_service.consume_messages.side_effect = test_exception
        
        # 执行run方法
        self.worker_node.run()
        
        # 验证logger.error被调用，记录错误信息
        self.worker_node.logger.error.assert_called_once()
        self.assertIn("运行时错误", self.worker_node.logger.error.call_args[0][0])
        self.assertIn("Test exception", self.worker_node.logger.error.call_args[0][0])

    def test_process_task(self):
        """测试process_task方法"""
        # 模拟process_task方法
        with patch.object(self.worker_node, 'init_executor') as mock_init_executor:
            def mock_init_executor_side_effect(name, task_config):
                print(f'init_executor_side_effect: {name}, {task_config}')
            mock_init_executor.side_effect = mock_init_executor_side_effect
            self.worker_node.process_task(task_config, properties={})

    # def setUp(self):
    #     self.mock_get_data_source_with_config = patch.object(DataSourceManager, 'get_data_source_with_config').start()
    #     def mock_get_data_source_side_effect(data_source_type_):
    #         if data_source_type_ == data_source_type.RABBITMQ.value:
    #             mock_rabbitmq_client = Mock()
    #             mock_rabbitmq_client.consume_message.return_value = None
    #             return mock_rabbitmq_client
    #         elif data_source_type_ == data_source_type.MONGODB.value:
    #             mongodb_conn = Mock()
    #             return mongodb_conn
    #         elif data_source_type_ == data_source_type.MINIO.value:
    #             minio_client = Mock()
    #             return minio_client
    #         else:
    #             raise ValueError(f"Unknown data source type: {data_source_type_}")
    #     self.mock_get_data_source_with_config.side_effect = mock_get_data_source_side_effect
        
    # def test_run(self):
    #     with patch.object(WorkerNode, 'process_task') as mock_process_task:
    #         mock_process_task.return_value = True
            
    #         worker_node = WorkerNode()
    #         worker_node.run()
            
    #         mock_process_task.assert_called_once()
            

if __name__ == '__main__':
    worker_node = WorkerNode()
    worker_node.run()