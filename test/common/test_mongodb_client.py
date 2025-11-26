import datetime

from context import common
from common.mongodb_client import MongoDBConnection, mongodb_conn
data1 = {
    "id": "1",
    "jump_from_url": "",
    "hr_index_url": "",
    "state": 0,
    'url': 'https://zhaopin.jd.com/web/job/job_info_list/3',
    'api_url': '',
    'need_headers': False,
    'request_params': {
        'url': "https://zhaopin.jd.com/web/job/job_list",
        'headers': {
            "referer": "https://zhaopin.jd.com/web/job/job_info_list/3"
        },
        'cookies': {
            "JSESSIONID": "0D9E36EE88A43018AA117ECA03FAF083.s1"
        },
        'data': {
            "pageIndex": "2",
            "pageSize": "10",
            "workCityJson": "[]",
            "jobTypeJson": "[]",
            "jobSearch": ""
        }
    },
    'marked_fields': {
        'page': 'pageIndex',
        'page_size': 'pageSize',
        'page_start': '',
        'page_end': '',
    },
    'parse_rule': {
        'url_rule': ''
    },
    # 插入时间 格式2023-08-01 00:00:00
    'insert_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    'update_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}

if __name__ == '__main__':
    mongodb_conn.connect()
    collection_name = "jd_config"
    collection = mongodb_conn.get_collection(collection_name)
    
    # 插入数据，设置id为主键
    # mongodb_conn.insert_one(collection_name, data1, {"id": "1"})
    
    # 查询数据
    # if collection is not None:
    #     data = collection.find_one({"id": "1"})
    #     print(data)
    
    # 查询status为0的前100条数据
    if collection is not None:
        data = collection.find({"state": 3}).limit(100)
        for item in data:
            print(item)
    
    # 删除集合
    # collection.drop()