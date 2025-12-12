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
    'pagination': [394,1],
    'parse_rule': {
        'url_rule'
    },
    'round': 0
}