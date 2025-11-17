import pytest
from unittest import mock
from common.mongodb_client import MongoDBConnection
import pymongo

class TestMongoDBConnection:
    def test_init(self):
        """测试初始化功能"""
        mongo_client = MongoDBConnection(
            host='test_host',
            port=1234,
            username='test_user',
            password='test_pass',
            db_name='test_db'
        )
        
        assert mongo_client.host == 'test_host'
        assert mongo_client.port == 1234
        assert mongo_client.username == 'test_user'
        assert mongo_client.password == 'test_pass'
        assert mongo_client.db_name == 'test_db'
        assert mongo_client.client is None
        assert mongo_client.db is None
    
    @mock.patch('pymongo.MongoClient')
    def test_connect_with_auth_success(self, mock_pymongo):
        """测试带认证的连接成功情况"""
        # 模拟MongoClient实例
        mock_client = mock_pymongo.return_value
        mock_client.admin.command.return_value = {}
        mock_client.__getitem__.return_value = mock.MagicMock()
        
        mongo_client = MongoDBConnection(
            host='localhost',
            port=27017,
            username='user',
            password='pass',
            db_name='test_db'
        )
        
        # 测试连接
        result = mongo_client.connect()
        
        assert result is True
        mock_pymongo.assert_called_once_with(
            host='localhost',
            port=27017,
            username='user',
            password='pass'
        )
        mock_client.admin.command.assert_called_once_with('ping')
        mock_client.__getitem__.assert_called_once_with('test_db')
    
    @mock.patch('pymongo.MongoClient')
    def test_connect_without_auth_success(self, mock_pymongo):
        """测试不带认证的连接成功情况"""
        # 模拟MongoClient实例
        mock_client = mock_pymongo.return_value
        mock_client.admin.command.return_value = {}
        mock_client.__getitem__.return_value = mock.MagicMock()
        
        mongo_client = MongoDBConnection(
            host='localhost',
            port=27017,
            db_name='test_db'
        )
        
        # 测试连接
        result = mongo_client.connect()
        
        assert result is True
        mock_pymongo.assert_called_once_with(host='localhost', port=27017)
    
    @mock.patch('pymongo.MongoClient')
    def test_connect_failure(self, mock_pymongo):
        """测试连接失败情况"""
        # 模拟连接失败
        mock_pymongo.side_effect = Exception("连接失败")
        
        mongo_client = MongoDBConnection()
        
        # 测试连接
        result = mongo_client.connect(max_retries=2)
        
        assert result is False
        assert mock_pymongo.call_count == 2
    
    def test_disconnect(self):
        """测试断开连接功能"""
        mongo_client = MongoDBConnection()
        mongo_client.client = mock.MagicMock()
        
        # 测试断开连接
        mongo_client.disconnect()
        
        mongo_client.client.close.assert_called_once()
    
    def test_get_collection(self):
        """测试获取集合功能"""
        # 测试未连接时的情况
        mongo_client = MongoDBConnection()
        assert mongo_client.get_collection('test_collection') is None
        
        # 测试已连接时的情况
        mock_db = mock.MagicMock()
        mock_db.__getitem__.return_value = 'test_collection_instance'
        mongo_client.db = mock_db
        
        collection = mongo_client.get_collection('test_collection')
        assert collection == 'test_collection_instance'
        mock_db.__getitem__.assert_called_once_with('test_collection')
    
    @mock.patch.object(MongoDBConnection, 'get_collection')
    def test_insert_one(self, mock_get_collection):
        """测试插入单条文档功能"""
        # 模拟集合和插入结果
        mock_collection = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_result.inserted_id = 'inserted_id'
        mock_collection.insert_one.return_value = mock_result
        mock_get_collection.return_value = mock_collection
        
        mongo_client = MongoDBConnection()
        
        # 测试插入
        result_id = mongo_client.insert_one('test_collection', {'key': 'value'})
        
        assert result_id == 'inserted_id'
        mock_get_collection.assert_called_once_with('test_collection')
        mock_collection.insert_one.assert_called_once_with({'key': 'value'})
    
    @mock.patch.object(MongoDBConnection, 'get_collection')
    def test_insert_one_failure(self, mock_get_collection):
        """测试插入单条文档失败情况"""
        # 模拟获取集合失败
        mock_get_collection.return_value = None
        
        mongo_client = MongoDBConnection()
        
        # 测试插入
        result_id = mongo_client.insert_one('test_collection', {'key': 'value'})
        
        assert result_id is None
    
    @mock.patch.object(MongoDBConnection, 'get_collection')
    def test_insert_many(self, mock_get_collection):
        """测试批量插入文档功能"""
        # 模拟集合和插入结果
        mock_collection = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_result.inserted_ids = ['id1', 'id2']
        mock_collection.insert_many.return_value = mock_result
        mock_get_collection.return_value = mock_collection
        
        mongo_client = MongoDBConnection()
        
        # 测试批量插入
        result_ids = mongo_client.insert_many('test_collection', [{'key1': 'value1'}, {'key2': 'value2'}])
        
        assert result_ids == ['id1', 'id2']
        mock_get_collection.assert_called_once_with('test_collection')
        mock_collection.insert_many.assert_called_once_with([{'key1': 'value1'}, {'key2': 'value2'}])