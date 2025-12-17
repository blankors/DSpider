
from context import common
import unittest
from unittest.mock import patch, MagicMock
from dspider.common.rabbitmq_service import RabbitMQClient, rabbitmq_client

class TestRabbitMQClient(unittest.TestCase):
    """RabbitMQ客户端的单元测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.rabbitmq_conn = RabbitMQClient(
            host='localhost',
            port=5672,
            username='test_user',
            password='test_password',
            virtual_host='/'
        )
    
    @patch('common.rabbitmq_client.pika.BlockingConnection')
    def test_connect_success(self, mock_connection):
        """测试成功连接"""
        # 模拟成功连接
        mock_conn_instance = MagicMock()
        mock_channel = MagicMock()
        mock_conn_instance.channel.return_value = mock_channel
        mock_connection.return_value = mock_conn_instance
        
        # 执行连接
        result = self.rabbitmq_conn.connect(max_retries=1)
        
        # 验证结果
        self.assertTrue(result)
        mock_connection.assert_called_once()
        mock_conn_instance.channel.assert_called_once()
    
    @patch('common.rabbitmq_client.pika.BlockingConnection')
    def test_connect_failure(self, mock_connection):
        """测试连接失败"""
        # 模拟连接失败
        mock_connection.side_effect = Exception("模拟连接失败")
        
        # 执行连接
        result = self.rabbitmq_conn.connect(max_retries=1)
        
        # 验证结果
        self.assertFalse(result)
        mock_connection.assert_called_once()
    
    def test_disconnect(self):
        """测试断开连接"""
        # 设置模拟连接
        self.rabbitmq_conn.connection = MagicMock()
        self.rabbitmq_conn.connection.is_open = True
        
        # 执行断开连接
        self.rabbitmq_conn.disconnect()
        
        # 验证连接被关闭
        self.rabbitmq_conn.connection.close.assert_called_once()

if __name__ == '__main__':
    # 运行单元测试
    # unittest.main()
    
    # 查询队列消息数量
    queue_name = 'test_queue'
    message_count = rabbitmq_client.get_queue_message_count(queue_name)
    print(f"队列 {queue_name} 中的消息数量: {message_count}")