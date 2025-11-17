import pytest
from unittest import mock
import json
import os
from common.logger_config import LoggerConfig
import logging

class TestLoggerConfig:
    @mock.patch('os.path.exists')
    @mock.patch('json.load')
    @mock.patch('logging.config.dictConfig')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('logging.getLogger')
    def test_setup_logger_with_config_file(self, mock_get_logger, mock_open, mock_dict_config, mock_json_load, mock_exists):
        """测试从配置文件加载日志配置"""
        # 模拟文件存在和配置内容
        mock_exists.return_value = True
        mock_json_load.return_value = {'loggers': {}}
        mock_logger = mock.MagicMock()
        mock_logger.name = 'test_logger'
        mock_get_logger.return_value = mock_logger
        
        # 测试配置加载
        logger = LoggerConfig.setup_logger('test_config.json', name='test_logger')
        
        # 验证调用
        mock_exists.assert_called_once_with('test_config.json')
        mock_open.assert_called_once_with('test_config.json', 'r', encoding='utf-8')
        mock_json_load.assert_called_once()
        mock_dict_config.assert_called_once_with({'loggers': {}})
        mock_get_logger.assert_called_once_with('test_logger')
        assert logger == mock_logger
    
    @mock.patch('os.path.exists')
    @mock.patch('logging.getLogger')
    @mock.patch('logging.StreamHandler')
    def test_setup_logger_with_default_config(self, mock_stream_handler, mock_get_logger, mock_exists):
        """测试使用默认配置"""
        # 模拟文件不存在
        mock_exists.return_value = False
        
        # 模拟logger和handler
        mock_logger = mock.MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger
        mock_handler = mock.MagicMock()
        mock_stream_handler.return_value = mock_handler
        
        # 测试默认配置
        logger = LoggerConfig.setup_logger('non_existent_config.json', log_level=logging.DEBUG, name='test_logger')
        
        # 验证调用
        mock_exists.assert_called_once_with('non_existent_config.json')
        mock_get_logger.assert_called_once_with('test_logger')
        mock_logger.setLevel.assert_called_once_with(logging.DEBUG)
        mock_stream_handler.assert_called_once()
        mock_logger.addHandler.assert_called_with(mock_handler)
        assert logger == mock_logger
    
    @mock.patch('os.path.exists')
    @mock.patch('json.load')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('logging.getLogger')
    @mock.patch('logging.StreamHandler')
    def test_setup_logger_config_file_error(self, mock_stream_handler, mock_get_logger, mock_open, mock_json_load, mock_exists):
        """测试配置文件加载失败情况"""
        # 模拟文件存在但加载失败
        mock_exists.return_value = True
        mock_json_load.side_effect = Exception("加载失败")
        
        # 模拟logger和handler
        mock_logger = mock.MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger
        mock_handler = mock.MagicMock()
        mock_stream_handler.return_value = mock_handler
        
        # 测试错误情况
        logger = LoggerConfig.setup_logger('error_config.json')
        
        # 验证调用
        mock_exists.assert_called_once_with('error_config.json')
        mock_open.assert_called_once_with('error_config.json', 'r', encoding='utf-8')
        mock_json_load.assert_called_once()
        mock_get_logger.assert_called_once_with(None)
        mock_logger.setLevel.assert_called()
        mock_stream_handler.assert_called_once()
        mock_logger.addHandler.assert_called_with(mock_handler)
        assert logger == mock_logger
    
    @mock.patch('os.path.exists')
    @mock.patch('os.makedirs')
    @mock.patch('logging.getLogger')
    @mock.patch('logging.StreamHandler')
    @mock.patch('logging.FileHandler')
    @mock.patch('os.path.dirname')
    def test_setup_logger_with_log_file(self, mock_dirname, mock_file_handler, mock_stream_handler, mock_get_logger, mock_makedirs, mock_exists):
        """测试使用日志文件配置"""
        # 模拟文件不存在
        mock_exists.return_value = False
        mock_dirname.return_value = 'logs'
        
        # 模拟logger和handler
        mock_logger = mock.MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger
        mock_stream = mock.MagicMock()
        mock_file = mock.MagicMock()
        mock_stream_handler.return_value = mock_stream
        mock_file_handler.return_value = mock_file
        
        # 测试带日志文件的配置
        logger = LoggerConfig.setup_logger(log_file='logs/test.log')
        
        # 验证调用
        mock_exists.assert_called_once()
        mock_dirname.assert_called_once_with('logs/test.log')
        mock_makedirs.assert_called_once_with('logs', exist_ok=True)
        mock_get_logger.assert_called_once_with(None)
        mock_stream_handler.assert_called_once()
        mock_file_handler.assert_called_once_with('logs/test.log', encoding='utf-8')
        assert logger == mock_logger
    
    @mock.patch('os.path.dirname')
    @mock.patch('os.path.exists')
    @mock.patch('logging.getLogger')
    @mock.patch('logging.StreamHandler')
    @mock.patch('logging.FileHandler')
    def test_setup_logger_without_log_dir(self, mock_file_handler, mock_stream_handler, mock_get_logger, mock_exists, mock_dirname):
        """测试不指定日志目录的情况"""
        # 模拟文件不存在和dirname返回空
        mock_exists.return_value = False
        mock_dirname.return_value = ''
        
        # 模拟logger和handler
        mock_logger = mock.MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger
        mock_stream = mock.MagicMock()
        mock_file = mock.MagicMock()
        mock_stream_handler.return_value = mock_stream
        mock_file_handler.return_value = mock_file
        
        # 测试无日志目录配置
        logger = LoggerConfig.setup_logger(log_file='test.log')
        
        # 验证调用
        mock_exists.assert_called_once()
        mock_dirname.assert_called_once_with('test.log')
        mock_get_logger.assert_called_once_with(None)
        mock_stream_handler.assert_called_once()
        mock_file_handler.assert_called_once_with('test.log', encoding='utf-8')
        assert logger == mock_logger
    
    def test_create_default_config(self):
        """测试创建默认配置"""
        config = LoggerConfig.create_default_config('test_default.log')
        
        # 验证配置结构
        assert config['version'] == 1
        assert config['disable_existing_loggers'] is False
        assert 'formatters' in config
        assert 'handlers' in config
        assert 'console' in config['handlers']
        
        # 验证日志文件路径
        if 'file' in config['handlers']:
            assert config['handlers']['file']['filename'] == 'test_default.log'