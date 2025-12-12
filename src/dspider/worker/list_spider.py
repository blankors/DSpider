import logging
import uuid
import time

import requests

from dspider.worker.judge_requests_method import ReqMethodHasPostJudger

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    def __init__(self, executor):
        self.executor = executor
        self.minio_client = executor.minio_client
        self.req_method_judger = ReqMethodHasPostJudger()
        self.pagination_getter = PaginationGetterDefault()
    
    def start(self, task: dict):
        task_id = task.get('_id', str(uuid.uuid4()))
     
        request_params = task['request_params']
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
            
            result = self.single_request(cur, step, api_url, headers, postdata, req_method, statistic)
            continue_, resp = result
            save_success = self.save()
            
            if not continue_:
                print(statistic)
                break
            
            cur += step
            time.sleep(5)


    def single_request(self, cur, step, api_url, headers, postdata, req_method, statistic):
        resp = requests.request(req_method, api_url, headers=headers, data=postdata)
        print(cur, resp.status_code, resp.text[-50:])
        statistic['total'] = statistic.get('total', 0) + 1
        last_fail = statistic.get('last_fail')
        last_resp_text = statistic.get('last_resp_text')
        
        if resp.status_code == 200:
            statistic['success'] = statistic.get('success', 0) + 1
            if resp.text == last_resp_text:
                statistic['stop_reason'] = f"重复页响应内容，最后成功页：{cur}"
                return False
            else:
                statistic['last_resp_text'] = resp.text
                return True
        else:
            if last_fail + step == cur: # 有连续页面请求失败
                statistic['stop_reason'] = f"连续页请求失败，最后失败页：{cur}"
                return False
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
        
    def store_to_minio(self, task_id: str, content: str, bucket_name: str = "spider-results") -> bool:
        """将内容存储到MinIO
        
        Args:
            task_id: 任务ID
            content: 要存储的内容
            bucket_name: 存储桶名称
            
        Returns:
            bool: 是否成功存储
        """
        try:
            # 生成唯一的对象名称
            import datetime
            object_name = f"{datetime.datetime.now().strftime('%Y/%m/%d')}/{task_id}.txt"
            
            # 存储到MinIO
            success = self.minio_client.upload_text(bucket_name, object_name, content)
            print(success)
            if success:
                self.logger.info(f"[{self.worker_id}] 成功将任务 {task_id} 的结果存储到MinIO: {object_name}")
            else:
                self.logger.error(f"[{self.worker_id}] 存储任务 {task_id} 的结果到MinIO失败")
            
            return success
        except Exception as e:
            self.logger.error(f"[{self.worker_id}] 存储到MinIO时发生错误: {str(e)}")
            return False

    def save(self):
        filepath = ''
        collection = None
        collection.insert(
            {
                'id'
                'path'
            }
        )