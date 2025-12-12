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
    def __init__(self):
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
            'stop_reason': ''
        }
        
        last_fail = -1
        last_resp_text = ''
        while True:
            if page_filed['location'] == 'api_url':
                api_url = api_url.format(cur)
            elif page_filed['location'] == 'postdata':
                postdata[page_filed['key']] = postdata_template[page_filed['key']].format(cur)
            resp = requests.request(req_method, api_url, headers=headers, data=postdata)
            print(cur, resp.status_code, resp.text[-50:])
            statistic['total'] = statistic.get('total', 0) + 1
            if statistic.get('fail'):
                last_fail = statistic.get('fail')[-1]
            if resp.status_code == 200:
                statistic['success'] = statistic.get('success', 0) + 1
                if resp.text == last_resp_text:
                    statistic['stop_reason'] = f"重复页响应内容，最后成功页：{cur}"
                    break
                last_resp_text = resp.text
            else:
                if last_fail + step == cur: # 有连续页面请求失败
                    statistic['stop_reason'] = f"连续页请求失败，最后失败页：{cur}"
                    break
                if statistic.get('fail'):
                    statistic['fail'].append(cur)
                else:
                    statistic['fail'] = [cur]
                
            cur += step
            time.sleep(5)
        
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
        
    # def req(self, task: dict) -> requests.Response:
    #     try:
    #         resp = requests.request(req_method, api_url, headers=headers, data=postdata)
            
    #         # 将响应内容存储到MinIO
    #         # self.store_to_minio(task_id, resp.text)
    #     except KeyError as e:
    #         self.logger.error(f"[{self.worker_id}] 任务缺少必要字段: {str(e)}")
    #         return False
    #     except Exception as e:
    #         self.logger.error(f"[{self.worker_id}] 处理任务时发生错误: {str(e)}")
    #         return False