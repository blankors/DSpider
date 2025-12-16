import sys
import os
import unittest
import json
import datetime
from unittest.mock import Mock, MagicMock, patch

from dspider.worker.spider.list_spider import PaginationGetterDefault
from dspider.worker.spider.list_spider import ListSpider, ListSpiderExtractorJson
# from dspider.worker.worker import WorkerNode, Executor

# Fix the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from test.test_data.data import jd_config, jd_config_tencent, jd_result_tencent, task_config

class TestPaginationGetterDefault(unittest.TestCase):
    def setUp(self):
        self.parse_rule_list = [1,1]
        
    def test_get_pagination(self):
        pagination_getter = PaginationGetterDefault()
        pagination = pagination_getter.get_pagination(self.parse_rule_list)
        self.assertEqual(pagination, self.parse_rule_list)

class TestListSpider(unittest.TestCase):
    def setUp(self):
        # Setup mock dependencies
        self.executor_mock = Mock()
        self.mongodb_service_mock = Mock()
        self.minio_client_mock = Mock()
        
        # Attach mocks to executor
        self.executor_mock.task_config = task_config
        self.executor_mock.mongodb_service = self.mongodb_service_mock
        self.executor_mock.minio_client = self.minio_client_mock
        
        # Create list spider instance
        self.list_spider = ListSpider(self.executor_mock)
        
        # Sample test data
        self.sample_resp_text = json.dumps(jd_result_tencent)
        
        self.task = jd_config_tencent
        self.parse_rule_list = self.task['parse_rule']['list_page']
    
    @patch('requests.request')
    @patch('dspider.worker.spider.list_spider.ListSpiderExtractorJson.extract_url')
    def test_single_request_success(self, mock_extract_url, mock_request):
        """Test successful single request"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.text = self.sample_resp_text
        mock_request.return_value = mock_resp
        mock_extract_url.return_value = ["https://example.com/1", "https://example.com/2"]
        
        statistic = {'stop_reason': '', 'last_fail': -1, 'fail': [], 'last_resp_text': ''}
        result = self.list_spider.single_request(
            "https://example.com/api", {"User-Agent": "test"}, {"page": 1}, "GET", 1, 1, statistic, self.parse_rule_list
        )
        
        mock_request.assert_called_once()
        self.assertEqual(result, mock_resp)
        self.assertEqual(statistic["total"], 1)
        self.assertEqual(statistic["success"], 1)
        self.assertEqual(statistic["last_resp_text"], self.sample_resp_text)

    @patch('requests.request')
    def test_single_request_failure(self, mock_request):
        """Test failed single request"""
        mock_resp = Mock()
        mock_resp.status_code = 404
        mock_resp.text = "Not Found"
        mock_request.return_value = mock_resp
        
        statistic = {'stop_reason': '', 'last_fail': -1, 'fail': [], 'last_resp_text': ''}
        result = self.list_spider.single_request(
            "https://example.com/api", {"User-Agent": "test"}, {"page": 1}, "GET", 1, 1, statistic, self.parse_rule_list
        )
        
        mock_request.assert_called_once()
        self.assertIsNone(result)
        self.assertEqual(statistic["total"], 1)
        self.assertEqual(statistic["fail"], [1])
        self.assertEqual(statistic["last_fail"], 1)

    @patch('requests.request')
    @patch('dspider.worker.spider.list_spider.ListSpiderExtractorJson.extract_url')
    def test_single_request_duplicate_content(self, mock_extract_url, mock_request):
        """Test single request with duplicate content"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.text = self.sample_resp_text
        mock_request.return_value = mock_resp
        mock_extract_url.return_value = ["https://example.com/1"]
        
        statistic = {'stop_reason': '', 'last_fail': -1, 'fail': [], 'last_resp_text': self.sample_resp_text}
        result = self.list_spider.single_request(
            "https://example.com/api", {"User-Agent": "test"}, {"page": 2}, "GET", 2, 1, statistic, self.parse_rule_list
        )
        
        mock_request.assert_called_once()
        self.assertIsNone(result)
        self.assertEqual(statistic["total"], 1)
        self.assertEqual(statistic["success"], 1)
        self.assertEqual(statistic["stop_reason"], "重复页响应内容，最后成功页：2")

    @patch('requests.request')
    def test_single_request_consecutive_failure(self, mock_request):
        """Test consecutive failed requests"""
        mock_resp = Mock()
        mock_resp.status_code = 404
        mock_resp.text = "Not Found"
        mock_request.return_value = mock_resp
        
        statistic = {'stop_reason': '', 'last_fail': 1, 'fail': [1], 'last_resp_text': ''}
        result = self.list_spider.single_request(
            "https://example.com/api", {"User-Agent": "test"}, {"page": 2}, "GET", 2, 1, statistic, self.parse_rule_list
        )
        
        mock_request.assert_called_once()
        self.assertIsNone(result)
        self.assertEqual(statistic["total"], 1)
        self.assertEqual(statistic["fail"], [1, 2])
        self.assertEqual(statistic["stop_reason"], "连续页请求失败，最后失败页：2")

    @patch.object(ListSpider, 'single_request')
    def test_start(self, mock_single_request):
        """Test start method"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.text = self.sample_resp_text
        mock_single_request.return_value = mock_resp
        
        self.executor_mock.minio_client.upload_text.return_value = True
        
        self.list_spider.start(self.task)
        
        # mock_single_request.assert_called_once() # 这句是为了确保single_request被调用了一次
        mock_single_request.assert_called()
        self.assertEqual(self.list_spider.statistic["total"], 1)
        self.assertEqual(self.list_spider.statistic["success"], 1)

if __name__ == '__main__':
    unittest.main()