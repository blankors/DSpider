import sys
import os

from dspider.worker.list_spider import ListSpider
from dspider.worker.worker import WorkerNode

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

print(sys.path)
from test_data.data import jd_config

# list_spider = ListSpider()
# list_spider.start(jd_config)

executor = WorkerNode()
list_spider = ListSpider(executor)
list_spider.start(jd_config)
