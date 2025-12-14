import datetime

task_config = {
    "task_name": "JD",
    "spider": [
        {
            "spider_name": "list",
            "p_num": 1,
            "queue_name": "list"
        },
        {
            "spider_name": "detail"
        }
    ]
}
jd_config = {
    "id": "1",
    "hr_index_url": "",
    "social_index_url": "https://zhaopin.jd.com/web/job/job_info_list/3",
    "need_headers": False,
    "request_params": {
        "api_url": "https://zhaopin.jd.com/web/job/job_list",
        "headers": {
            "referer": "https://zhaopin.jd.com/web/job/job_info_list/3",
        },
        "cookies": {
            "JSESSIONID": "0D9E36EE88A43018AA117ECA03FAF083.s1"
        },
        "postdata": {
            "pageIndex": "{0}",
            "pageSize": "10",
            "workCityJson": "[]",
            "jobTypeJson": "[]",
            "jobSearch": ""
        },
        "additional": {
            "index_api_url": "",
            "index_postdata": {}
        }
    },
    "pagination": [397,1],
    "parse_rule": {
        "list_page": {
            "list_data": "result.list",
            "url_rule": {
                "url_path": "https://careers.pddglobalhr.com/jobs/detail",
                "params": {"code": "code"},
                "postdata": {}
            }
            # https://careers.pddglobalhr.com/jobs/detail?code=I020206&type=fulltime
            # url -> url + {code: I020206, type: fulltime}
            # 根据I020206，去listitem中找这个字符串，得到对应的key
            # 计算这个key在listitem json的路径：list_item[0].code
            # "url_rule": {"code": "code", "type": "type"}
            # 意思是 {list_item中的key: url中params或postdata的key}
        },
        "detail_page": {
        }
    },
    "schedule": {
        "type": "", # 
        "interval": 10
    }
}
jd_config_pdd = {
    "id": "1",
    "hr_index_url": "",
    "social_index_url": "https://careers.pddglobalhr.com/jobs",
    "need_headers": False,
    "request_params": {
        "api_url": "https://careers.pddglobalhr.com/api/recruit/position/list",
        "headers": {
            "referer": "https://careers.pddglobalhr.com/jobs",
        },
        "cookies": {
            "JSESSIONID": "0D9E36EE88A43018AA117ECA03FAF083.s1"
        },
        "postdata": {
            "pageIndex": "{0}",
            "pageSize": "10",
            "workCityJson": "[]",
            "jobTypeJson": "[]",
            "jobSearch": ""
        },
        "additional": {
            "index_api_url": "",
            "index_postdata": {}
        }
    },
    "pagination": [397,1],
    "parse_rule": {
        "list_page": {
            "list_data": "result.list",
            "url_rule": {
                "url_path": "https://careers.pddglobalhr.com/jobs/detail",
                "params": {"code": "code"},
                "postdata": {}
            }
            # https://careers.pddglobalhr.com/jobs/detail?code=I020206&type=fulltime
            # url -> url + {code: I020206, type: fulltime}
            # 根据I020206，去listitem中找这个字符串，得到对应的key
            # 计算这个key在listitem json的路径：list_item[0].code
            # "url_rule": {"code": "code", "type": "type"}
            # 意思是 {list_item中的key: url中params或postdata的key}
        },
        "detail_page": {
        }
    },
    "schedule": {
        "type": "", # 
        "interval": 10
    }
}
jd_config_tencent = {
    "id": "1",
    "hr_index_url": "https://careers.tencent.com/home.html",
    "social_index_url": "https://careers.tencent.com/search.html?query=at_1",
    "need_headers": False,
    "request_params": {
        "api_url": "https://careers.tencent.com/tencentcareer/api/post/Query?timestamp=&countryId=&cityId=&bgIds=&productId=&categoryId=&parentCategoryId=&attrId=1&keyword=&pageIndex={0}&pageSize=10&language=zh-cn&area=cn",
        "headers": {
            "referer": "https://careers.tencent.com/search.html?query=at_1",
        },
        "cookies": {},
        "postdata": {},
        "additional": {
            "index_api_url": "",
            "index_postdata": {}
        }
    },
    "pagination": [1,1],
    "parse_rule": {
        "list_page": {
            "list_data": "Data.Posts",
            "url_rule": {
                "url_path": "http://careers.tencent.com/jobdesc.html",
                "params": {"PostId": "postId"},
                "postdata": {}
            }
            # https://careers.pddglobalhr.com/jobs/detail?code=I020206&type=fulltime
            # url -> url + {code: I020206, type: fulltime}
            # 根据I020206，去listitem中找这个字符串，得到对应的key
            # 计算这个key在listitem json的路径：list_item[0].code
            # "url_rule": {"code": "code", "type": "type"}
            # 意思是 {list_item中的key: url中params或postdata的key}
        },
        "detail_page": {
        }
    },
    "schedule": {
        "type": "", # 
        "interval": 10
    }
}
jd_round = {
    "id": "",
    "jd_config_id": "",
    "round": 1, # 什么情况作为一轮，由于数据异常的重试要算作一轮吗？
    "round_datetime": 0,
    "statistic": {
        
    }
}

list_ = {
    "id": "",
    "jd_config_id": "",
    "round": 1,
    "page": 1, # 列表的第n页
               # 实际页码还是页码参数
    "file_path": "",
    
}
detail_ = {
    "in_page": 2, # 在列表的第几页
    "round": 1
}

# 历史版本
config_data = {
    "id": "5",
    "jump_from_url": "",
    "hr_index_url": "",
    "state": 0,
    'url': 'https://zhaopin.jd.com/web/job/job_info_list/3',
    'api_url': '',
    'need_headers': False,
    'request_params': {
        'api_url': "https://zhaopin.jd.com/web/job/job_list",
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