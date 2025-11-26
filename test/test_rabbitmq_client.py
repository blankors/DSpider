import pytest
from unittest import mock
from common.rabbitmq_client import RabbitMQClient
import pika

class TestRabbitMQConnection:
    def test_init(self):
        """测试初始化功能"""
        rabbit_client = RabbitMQClient(
            host='test_host',
            port=5672,
            username='test_user',
            password='test_pass',
            virtual_host='/test'
        )
        
        assert rabbit_client.host == 'test_host'
        assert rabbit_client.port == 5672
        assert rabbit_client.username == 'test_user'
        assert rabbit_client.password == 'test_pass'
        assert rabbit_client.virtual_host == '/test'
        assert rabbit_client.connection is None
        assert rabbit_client.channel is None
    
    @mock.patch('pika.BlockingConnection')
    def test_connect_success(self, mock_blocking_connection):
        """测试连接成功情况"""
        # 模拟连接实例
        mock_connection = mock_blocking_connection.return_value
        mock_channel = mock.MagicMock()
        mock_connection.channel.return_value = mock_channel
        
        rabbit_client = RabbitMQClient()
        
        # 测试连接
        result = rabbit_client.connect()
        
        assert result is True
        # 验证调用参数
        mock_blocking_connection.assert_called_once()
        call_args = mock_blocking_connection.call_args[0][0]
        assert call_args.host == 'localhost'
        assert call_args.port == 5672
        assert call_args.virtual_host == '/'
        assert call_args.credentials.username == 'guest'
        assert call_args.credentials.password == 'guest'
        
        mock_connection.channel.assert_called_once()
        assert rabbit_client.connection == mock_connection
        assert rabbit_client.channel == mock_channel
    
    @mock.patch('pika.BlockingConnection')
    def test_connect_failure(self, mock_blocking_connection):
        """测试连接失败情况"""
        # 模拟连接失败
        mock_blocking_connection.side_effect = Exception("连接失败")
        
        rabbit_client = RabbitMQClient()
        
        # 测试连接
        result = rabbit_client.connect(max_retries=2)
        
        assert result is False
        assert mock_blocking_connection.call_count == 2
    
    def test_disconnect(self):
        """测试断开连接功能"""
        rabbit_client = RabbitMQClient()
        
        # 测试没有连接的情况
        rabbit_client.disconnect()
        
        # 测试有连接的情况
        mock_connection = mock.MagicMock()
        mock_connection.is_open = True
        rabbit_client.connection = mock_connection
        
        rabbit_client.disconnect()
        mock_connection.close.assert_called_once()
    
    def test_declare_queue_success(self):
        """测试声明队列成功情况"""
        rabbit_client = RabbitMQClient()
        rabbit_client.channel = mock.MagicMock()
        
        # 测试声明队列
        result = rabbit_client.declare_queue('test_queue')
        
        assert result is True
        rabbit_client.channel.queue_declare.assert_called_once_with(
            queue='test_queue',
            durable=True,
            exclusive=False,
            auto_delete=False,
            arguments=None
        )
    
    def test_declare_queue_with_channel_none(self):
        """测试没有channel时声明队列的情况"""
        rabbit_client = RabbitMQClient()
        
        # 测试声明队列
        result = rabbit_client.declare_queue('test_queue')
        
        assert result is False
    
    def test_declare_exchange_success(self):
        """测试声明交换机成功情况"""
        rabbit_client = RabbitMQClient()
        rabbit_client.channel = mock.MagicMock()
        
        # 测试声明交换机
        result = rabbit_client.declare_exchange('test_exchange', 'direct')
        
        assert result is True
        rabbit_client.channel.exchange_declare.assert_called_once_with(
            exchange='test_exchange',
            exchange_type='direct',
            durable=True,
            auto_delete=False
        )
    
    def test_bind_queue_success(self):
        """测试绑定队列成功情况"""
        rabbit_client = RabbitMQClient()
        rabbit_client.channel = mock.MagicMock()
        
        # 测试绑定队列
        result = rabbit_client.bind_queue('test_queue', 'test_exchange', 'test_key')
        
        assert result is True
        rabbit_client.channel.queue_bind.assert_called_once_with(
            queue='test_queue',
            exchange='test_exchange',
            routing_key='test_key'
        )
    
    @mock.patch('json.dumps')
    @mock.patch('pika.BasicProperties')
    def test_publish_message_dict(self, mock_basic_properties, mock_json_dumps):
        """测试发布字典类型消息"""
        # 模拟
        mock_basic_properties.return_value = 'test_properties'
        mock_json_dumps.return_value = '{"key":"value"}'
        
        rabbit_client = RabbitMQClient()
        rabbit_client.channel = mock.MagicMock()
        
        # 测试发布消息
        message = {'key': 'value'}
        result = rabbit_client.publish_message('test_exchange', 'test_key', message)
        
        assert result is True
        mock_json_dumps.assert_called_once_with(message, ensure_ascii=False)
        mock_basic_properties.assert_called_once_with(delivery_mode=2)
        rabbit_client.channel.basic_publish.assert_called_once_with(
            exchange='test_exchange',
            routing_key='test_key',
            body='{"key":"value"}'.encode('utf-8'),
            properties='test_properties'
        )
    
    @mock.patch('pika.BasicProperties')
    def test_publish_message_string(self, mock_basic_properties):
        """测试发布字符串类型消息"""
        # 模拟
        mock_basic_properties.return_value = 'test_properties'
        
        rabbit_client = RabbitMQClient()
        rabbit_client.channel = mock.MagicMock()
        
        # 测试发布消息
        message = 'test_message'
        result = rabbit_client.publish_message('test_exchange', 'test_key', message, persistent=False)
        
        assert result is True
        mock_basic_properties.assert_called_once_with(delivery_mode=1)
        rabbit_client.channel.basic_publish.assert_called_once_with(
            exchange='test_exchange',
            routing_key='test_key',
            body='test_message'.encode('utf-8'),
            properties='test_properties'
        )