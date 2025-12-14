import logging
import uuid
import time
import typing
import datetime
import json

import requests

from dspider.worker.judge_requests_method import ReqMethodHasPostJudger

if typing.TYPE_CHECKING:
    from dspider.worker.worker import WorkerNode

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class PaginationGetter:
    """
    分页获取器基类
    """
    def __init__(self):
        pass
    
    def get_pagination(self, task: dict) -> list:
        """
        获取分页信息
        :param task: 任务字典
        :return: 分页信息列表。[1,1]代表起始位置与步长
        :raises KeyError: 如果任务字典中缺少pagination字段
        """
        pass

class PaginationGetterDefault(PaginationGetter):
    def __init__(self):
        pass
    
    def get_pagination(self, task: dict) -> list:
        page = {
            "pageIndex": "2",
            "pageSize": "10",
            "workCityJson": "[]",
            "jobTypeJson": "[]",
            "jobSearch": ""
        }
        return task['pagination']
    
class ListSpider:
    def __init__(self, executor: 'WorkerNode'):
        self.executor = executor
        self.mongodb_service = executor.mongodb_service
        self.minio_client = executor.minio_client
        self.req_method_judger = ReqMethodHasPostJudger()
        self.pagination_getter = PaginationGetterDefault()
        self.logger = logging.getLogger(__name__)
    
    def start(self, task: dict):
        task_id = task.get('_id', str(uuid.uuid4()))
     
        request_params = task['request_params']
        parse_rule_list = task['parse_rule']['list_page']
        api_url, headers, postdata_template = request_params['api_url'], request_params['headers'], request_params['postdata']
        postdata = postdata_template.copy()
        req_method = self.req_method_judger.judge(task)
        pagination = self.pagination_getter.get_pagination(task)
        start, cur, step = pagination[0], pagination[0], pagination[1]
        
        additional_params = request_params['additional']
        if additional_params['index_api_url'] != '' or \
            additional_params['index_postdata'] != {}:
                api_url = additional_params['index_api_url']
                postdata = additional_params['index_postdata']
        
        page_filed = self.get_page_filed(task)
        statistic = {
            'stop_reason': '',
            'last_fail': -1,
            'fail': [],
            'last_resp_text': ''
        }

        while True:
            if page_filed['location'] == 'api_url':
                api_url = api_url.format(cur)
            elif page_filed['location'] == 'postdata':
                postdata[page_filed['key']] = postdata_template[page_filed['key']].format(cur)
            
            resp = self.single_request(api_url, headers, postdata, req_method, cur, step, statistic, parse_rule_list)
            
            if not resp:
                break
            else:
                save_info = self.get_save_info(task, resp.text)
                self.store_to_minio(save_info['filepath'], resp.text)
                save_success = self.save(save_info['filepath'])
            
            cur += step
            time.sleep(5)

    def get_save_info(self, task, resp_text):
        """ 
        输入：任务信息+响应信息
        输出：
        
        :param task: 任务字典
        :return: None
        """
        task_id = task.get('_id', str(uuid.uuid4()))
        import hashlib
        md5 = hashlib.md5(resp_text.encode('utf-8')).hexdigest()
        filepath = f"{datetime.datetime.now().strftime('%Y/%m/%d')}/{task_id}_{md5}.txt" # 示例：2023/08/25/123456.txt
        return {
            'filepath': filepath
        }

    def single_request(self, api_url, headers, postdata, req_method, cur, step, statistic, parse_rule_list):
        resp = requests.request(req_method, api_url, headers=headers, data=postdata)
        print(cur, resp.status_code, resp.text[-50:])
        statistic['total'] = statistic.get('total', 0) + 1
        last_fail = statistic.get('last_fail')
        last_resp_text = statistic.get('last_resp_text')
        
        if resp.status_code == 200:
            statistic['success'] = statistic.get('success', 0) + 1
            if resp.text == last_resp_text:
                statistic['stop_reason'] = f"重复页响应内容，最后成功页：{cur}"
                return None
            else:
                statistic['last_resp_text'] = resp.text
                resp_json = json.loads(resp.text)
                
                list_items_rule = parse_rule_list['list_data']
                path = list_items_rule.split('.')
                list_items: list = resp_json
                for p in path:
                    list_items = list_items.get(p)
                    print(list_items, path)
                
                url_rule = parse_rule_list['url_rule']
                url_path, params, postdata = url_rule['url_path'], url_rule['params'], url_rule['postdata']
                for item in list_items:
                    target_url = url_path
                    if postdata == {}:
                        target_url += '?'
                        for list_data_key, url_key in params.items():
                            target_url += f"{url_key}={item.get(list_data_key)}&" # TODO: 是否要考虑参数在目标URL的位置
                        target_url = target_url[:-1] # 去掉最后一个&
                        item['url'] = target_url
                print(list_items)
                return resp
        else:
            if last_fail + step == cur: # 有连续页面请求失败
                statistic['stop_reason'] = f"连续页请求失败，最后失败页：{cur}"
                return None
            statistic['fail'].append(cur)
            statistic['last_fail'] = cur
        
    def get_page_filed(self, task):
        api_url = task['request_params']['api_url']
        postdata = task['request_params']['postdata']
        
        if '{0}' in api_url:
            return {
                'location': 'api_url',
                'key': ''
            }
        for k, v in postdata.items():
            if '{0}' in v:
                return {
                    'location': 'postdata',
                    'key': k
                }
        
    def store_to_minio(self, object_name: str, content: str, bucket_name: str = "spider-results") -> bool:
        """将内容存储到MinIO
        
        Args:
            task_id: 任务ID
            content: 要存储的内容
            bucket_name: 存储桶名称
            
        Returns:
            bool: 是否成功存储
        """
        success = self.minio_client.upload_text(bucket_name, object_name, content)
        print(success)

    def save(self, filepath: str) -> bool:
        """将列表页路径保存到MongoDB
        
        Args:
            filepath: 列表页路径
            
        Returns:
            bool: 是否成功保存
        """
        collection = self.mongodb_service.get_collection('list')
        result = collection.insert_one(
            {
                'id': str(uuid.uuid4()),
                'path': filepath
            }
        )
        return result.acknowledged
