import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dspider.worker.spider.list_spider import ListSpider
from dspider.worker.worker import Executor


print(sys.path)
from test_data.data import jd_config, jd_config_tencent

# list_spider = ListSpider()
# list_spider.start(jd_config)

executor = Executor('ListSpider')
executor.process_task(jd_config_tencent, {})
