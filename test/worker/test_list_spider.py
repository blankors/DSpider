from dspider.worker.list_spider import ListSpider

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

print(sys.path)
from test_data.data import jd_config

list_spider = ListSpider()
list_spider.start(jd_config)

