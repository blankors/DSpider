import datetime
import sys
import requests

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__))) # 添加/.../.../test

from context import mongodb_conn, MongoDBConnection, mongodb_config

try:
    mongodb_conn = MongoDBConnection(
        host='localhost',
        port=mongodb_config.get('port', 27017),
        username=mongodb_config.get('username', None),
        password=mongodb_config.get('password', None),
        db_name=mongodb_config.get('db_name', 'spider_db'),
    )
    mongodb_conn.connect()
except Exception as e:
    print(f"MongoDB连接失败: {str(e)}")



# cookie data
cookie_data = {
    "id": "1",
    "url": "https://zhaopin.jd.com/web/job/job_info_list/3",
    "cookies": {
        "JSESSIONID": "0D9E36EE88A43018AA117ECA03FAF083.s1"
    }
}

if __name__ == '__main__':
    # 获取命令行参数
    action = ""
    collection_name_list = ["jd_config", "cookies", "recruitment_datasource_config"]
    collection_idx = 2
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if len(sys.argv) > 2:
            collection_idx = sys.argv[2]
            
    collection = mongodb_conn.get_collection(collection_name_list[collection_idx])
    
    if action == "add":
        from test_data.data import jd_config
        # 插入数据，设置id为主键
        # mongodb_conn.insert_one(collection_name, config_data)
        # cookie_collection.insert_one(cookie_data)
        collection.insert_one(jd_config)
    
    if action == "u":
        # 更新数据。更新id为5的配置，将state设置为1
        # collection.update_one({"id": "5"}, {"$set": {"state": 1}})
        # 设置request_params.data字段为空字典
        collection.update_one({"id": "5"}, {"$set": {"request_params.data": {}}})
        # 删除request_params.data字段
        # collection.update_one({"id": "5"}, {"$unset": {"request_params.data": ""}})
    
    # 删除集合
    if action == "rm":
        collection.drop()
        collection.drop()

    # 查询数据
    # if collection is not None:
    #     data = collection.find_one({"id": "1"})
    #     print(data)
    
    # 查询status为0的前100条数据
    # data = collection.find({"state": 3}).limit(100)
    data = collection.find()
    for item in data:
        print(item)
        
        api_url = item['request_params']['api_url']
        headers = item['request_params']['headers']
        data = item['request_params']['postdata']
        print(f'type(api_url): {type(api_url)}, type(headers): {type(headers)}, type(data): {type(data)}')
        print(f'api_url: {api_url}, headers: {headers}, data: {data}')
        
        
        # data = {
        #     'pageIndex': '1',
        #     'pageSize': '10',
        #     'workCityJson': '[]',
        #     'jobTypeJson': '[]',
        #     'jobSearch': '',
        # }
        # response = requests.post('https://zhaopin.jd.com/web/job/job_list', headers=headers, data=data) # 仅校验header是否正确
        # response = requests.post(api_url, headers=headers, data=data)
        # print(response.text)