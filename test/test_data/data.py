task_config = {
    'task_name': 'JD',
    'spider': [
        {
            'spider_name': 'list',
            'p_num': 1,
            'queue_name': 'list'
        },
        {
            'spider_name': 'detail'
        }
    ]
}
jd_config = {
    "id": "1",
    "hr_index_url": "",
    "social_index_url": "https://zhaopin.jd.com/web/job/job_info_list/3",
    'need_headers': False,
    'request_params': {
        'api_url': "https://zhaopin.jd.com/web/job/job_list",
        'headers': {
            "referer": "https://zhaopin.jd.com/web/job/job_info_list/3",
        },
        'cookies': {
            "JSESSIONID": "0D9E36EE88A43018AA117ECA03FAF083.s1"
        },
        'postdata': {
            "pageIndex": "{0}",
            "pageSize": "10",
            "workCityJson": "[]",
            "jobTypeJson": "[]",
            "jobSearch": ""
        },
        'additional': {
            'index_api_url': '',
            'index_postdata': {}
        }
    },
    'pagination': [397,1],
    'parse_rule': {
        'url_rule'
    },
    'schedule': {
        'type': '', # 
        'interval': 10
    }
}
jd_round = {
    'id': '',
    'jd_config_id': '',
    'round': 1, # 什么情况作为一轮，由于数据异常的重试要算作一轮吗？
    'round_datetime': 0,
    'statistic': {
        
    }
}

list_ = {
    'id': '',
    'jd_config_id': '',
    'round': 1,
    'page': 1, # 列表的第n页
               # 实际页码还是页码参数
    'file_path': '',
    
}
detail_ = {
    'in_page': 2, # 在列表的第几页
    'round': 1
}