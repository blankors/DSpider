import unittest
from unittest.mock import Mock
from unittest.mock import patch
import sys
import os

# from context import worker
from dspider.worker.worker import WorkerNode, Executor
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
        # 该测试logger必须是mock的
        # self.worker_node.logger.info.assert_called_once()
        # self.assertIn("用户中断", self.worker_node.logger.info.call_args[0][0])
    
    def test_run_exception(self):
        """测试run方法捕获其他异常"""
        # 模拟consume_messages抛出异常
        test_exception = Exception("Test exception")
        self.mock_rabbitmq_service.consume_messages.side_effect = test_exception
        
        # 执行run方法
        self.worker_node.run()
        
        # 验证logger.error被调用，记录错误信息
        # self.worker_node.logger.error.assert_called_once()
        # self.assertIn("运行时错误", self.worker_node.logger.error.call_args[0][0])
        # self.assertIn("Test exception", self.worker_node.logger.error.call_args[0][0])

    def test_process_task(self):
        """测试process_task方法"""
        # 模拟init_executor方法
        # with patch.object(self.worker_node, 'init_executor') as mock_init_executor:
        #     def mock_init_executor_side_effect(name, task_config):
        #         print(f'init_executor_side_effect: {name}, {task_config}')
        #     mock_init_executor.side_effect = mock_init_executor_side_effect
        #     self.worker_node.process_task(task_config, properties={})
        
        # 模拟Executor.run方法
        with patch.object(Executor, 'run') as mock_run:
            def mock_run_side_effect():
                print(self.worker_node.executor.executor_id)
                return True
            mock_run.side_effect = mock_run_side_effect
            self.worker_node.process_task(task_config, properties={})
            
    def test_init_executor(self):
        """测试init_executor方法，确保不连接真实数据源"""
        spider_name = "ListSpider"
        with patch('dspider.worker.worker.Executor') as mock_executor:
            mock_executor_instance = Mock()
            mock_executor.return_value = mock_executor_instance

            self.worker_node.init_executor(spider_name, task_config)
            
            # 验证Executor被正确实例化
            mock_executor.assert_called_once_with(spider_name, task_config)
            mock_executor_instance.run.assert_called_once()

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

class TestExecutor(unittest.TestCase):
    
    def setUp(self):
        """设置测试环境"""
        # 测试参数
        self.spider_name = "ListSpider"
        self.task_config = {
            "spider": {
                self.spider_name: {
                    "queue_name": "test_queue",
                    "prefetch_count": 1
                }
            },
            "datasource": {
                "list_page": "list_page",
                "bucket_name": "spider-results"
            }
        }
        
        # 模拟数据源管理器
        self.mock_data_source_manager = patch('dspider.worker.worker.DataSourceManager').start()
        
        # 模拟各种数据源
        self.mock_rabbitmq_client = Mock()
        self.mock_mongodb_service = Mock()
        self.mock_minio_client = Mock()
        
        # 设置数据源管理器的行为
        def mock_get_data_source_side_effect(data_source_type_):
            if data_source_type_ == data_source_type.RABBITMQ.value:
                return self.mock_rabbitmq_client
            elif data_source_type_ == data_source_type.MONGODB.value:
                return self.mock_mongodb_service
            elif data_source_type_ == data_source_type.MINIO.value:
                return self.mock_minio_client
            return Mock()
        
        self.mock_data_source_manager.return_value.get_data_source_with_config.side_effect = mock_get_data_source_side_effect
        
        # 模拟walk_modules函数
        self.mock_walk_modules = patch('dspider.worker.worker.walk_modules').start()
        
        # 模拟spider类
        self.mock_spider_class = Mock()
        self.mock_spider_instance = Mock()
        self.mock_spider_class.return_value = self.mock_spider_instance
        
        # 设置模块的行为
        self.mock_module = Mock()
        setattr(self.mock_module, self.spider_name, self.mock_spider_class)
        self.mock_walk_modules.return_value = [self.mock_module]
        
        # 模拟uuid
        # self.mock_uuid = patch('uuid.uuid4').start()
        # self.mock_uuid.return_value = Mock(hex="test-uuid")
        
        # 模拟logger
        # self.mock_logger = patch('logging.getLogger').start()
        # self.mock_logger_instance = Mock()
        # self.mock_logger.return_value = self.mock_logger_instance
        
    def tearDown(self):
        """清理测试环境"""
        patch.stopall()
    
    def test_init(self):
        """测试Executor初始化"""
        # 创建Executor实例
        executor = Executor(self.spider_name, self.task_config)
        
        # 验证数据源管理器被调用
        self.mock_data_source_manager.assert_called_once()
        
        # 验证数据源获取方法被调用
        data_source_manager_instance = self.mock_data_source_manager.return_value
        data_source_manager_instance.get_data_source_with_config.assert_any_call(data_source_type.RABBITMQ.value)
        data_source_manager_instance.get_data_source_with_config.assert_any_call(data_source_type.MONGODB.value)
        data_source_manager_instance.get_data_source_with_config.assert_any_call(data_source_type.MINIO.value)
        
        # 验证walk_modules被调用
        self.mock_walk_modules.assert_called_once_with('dspider.worker.spider')
        
        # 验证spider类被实例化
        self.mock_spider_class.assert_called_once_with(executor)
        
        # 验证属性设置
        self.assertEqual(executor.spider_name, self.spider_name)
        self.assertEqual(executor.task_config, self.task_config)
        self.assertEqual(executor.queue_name, "test_queue")
        self.assertEqual(executor.prefetch_count, 1)
        self.assertEqual(executor.executor_id, "test-uuid")
    
    def test_init_spider_not_found(self):
        """测试当spider不存在时的初始化"""
        # 设置walk_modules返回一个不包含spider的模块
        self.mock_walk_modules.return_value = [Mock()]
        
        # 验证抛出ImportError
        with self.assertRaises(ImportError):
            Executor(self.spider_name, self.task_config)
    
    def test_run(self):
        """测试run方法"""
        # 创建Executor实例
        executor = Executor(self.spider_name, self.task_config)
        
        # 调用run方法
        executor.run()
        
        # 验证consume_messages被调用
        self.mock_rabbitmq_client.consume_messages.assert_called_once_with(
            executor.queue_name,
            callback=executor.process_task,
            auto_ack=False,
            prefetch_count=executor.prefetch_count
        )
    
    def test_run_keyboard_interrupt(self):
        """测试run方法处理KeyboardInterrupt"""
        # 创建Executor实例
        executor = Executor(self.spider_name, self.task_config)
        
        # 模拟KeyboardInterrupt
        self.mock_rabbitmq_client.consume_messages.side_effect = KeyboardInterrupt()
        
        # 验证run方法正确处理异常
        with self.assertRaises(KeyboardInterrupt):
            executor.run()
    
    def test_run_exception(self):
        """测试run方法处理其他异常"""
        # 创建Executor实例
        executor = Executor(self.spider_name, self.task_config)
        
        # 模拟一般异常
        test_exception = Exception("Test exception")
        self.mock_rabbitmq_client.consume_messages.side_effect = test_exception
        
        # 验证run方法正确处理异常
        with self.assertRaises(Exception):
            executor.run()
    
    def test_process_task_success(self):
        """测试process_task方法成功处理任务"""
        # 创建Executor实例
        executor = Executor(self.spider_name, self.task_config)
        
        # 测试任务
        test_task = {"_id": "test-task"}
        test_properties = {}
        
        # 调用process_task方法
        result = executor.process_task(test_task, test_properties)
        
        # 验证spider.start被调用
        self.mock_spider_instance.start.assert_called_once_with(test_task)
        
        # 验证返回值
        self.assertTrue(result)
    
    def test_process_task_failure(self):
        """测试process_task方法处理任务失败"""
        # 创建Executor实例
        executor = Executor(self.spider_name, self.task_config)
        
        # 测试任务
        test_task = {"_id": "test-task"}
        test_properties = {}
        
        # 模拟spider.start抛出异常
        test_exception = Exception("Test exception")
        self.mock_spider_instance.start.side_effect = test_exception
        
        # 调用process_task方法
        result = executor.process_task(test_task, test_properties)
        
        # 验证spider.start被调用
        self.mock_spider_instance.start.assert_called_once_with(test_task)
        
        # 验证返回值
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()