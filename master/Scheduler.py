import random
import time
import re
import logging
from logging.handlers import TimedRotatingFileHandler
import json
import traceback
from typing import Callable, List
import logging

import pika
from pika.exceptions import ChannelClosedByBroker, ChannelWrongStateError, ConnectionClosed, ConnectionClosedByBroker, IncompatibleProtocolError, StreamLostError
from pika import BasicProperties, BlockingConnection, ConnectionParameters, PlainCredentials, spec
from pika.adapters.blocking_connection import BlockingChannel

from common.mongodb_client import MongoDBConnection, mongodb_conn

# import pymssql

from master.master_config import master_config
from common.rabbitmq_client import RabbitMQClient, rabbitmq_client
# from qianshui.utils.db_manager import DBManager
from common.mysql_client import MySQLConnection, mysql_conn


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # TimedRotatingFileHandler('scheduler.log', when='midnight', backupCount=7),
        logging.StreamHandler()
    ]
)

system_logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self):
        self.sql_select_count = master_config['sql_select_count']
        self.sql_select_frenquency = master_config['sql_select_frenquency']

        self.queue_name = master_config['queue_name']
        self.rabbit = rabbitmq_client
        self.db = mysql_conn
        self.mongodb = mongodb_conn
        self.collection_name = "jd_config"
        self.collection = mongodb_conn.get_collection(self.collection_name)
        
        self.env_init()
    
    def env_init(self):
        self.rabbit.declare_priority_queue(self.queue_name)
    
    def send_to_queue(self, sql_result: List[dict]):
        # 记录成功发送的消息ID，用于批量更新状态
        sent_ids = []
        
        try:
            for data in sql_result:
                try:
                    # 发送到队列前验证数据格式
                    
                    # 发送消息并确保送达（利用RabbitMQ的confirm_delivery机制）
                    self.rabbit.publish_workqueue(
                        json.dumps(data, ensure_ascii=False), 
                        self.queue_name, 
                        priority=data.get('priority', 0)
                    )
                    sent_ids.append(data.get('id'))
                except Exception as e:
                    system_logger.error(f'发送单条消息失败：{e}, 记录ID: {data.get("id")}')
                    # 根据异常类型决定是否重试
                    if isinstance(e, (StreamLostError, ConnectionClosedByBroker)):
                        system_logger.warning('检测到连接问题，尝试重置连接...')
                        self.rabbit.reset_connection()
            
            # 批量更新成功发送的消息状态
            if sent_ids:
                try:
                    self.update_message_status(sent_ids)
                    system_logger.info(f'已发送并更新状态：{len(sent_ids)}条数据')
                except Exception as db_error:
                    system_logger.error(f'更新数据库状态失败：{db_error}')
                    self.handle_update_failure(sent_ids)
            else:
                system_logger.warning('没有成功发送的消息需要更新状态')
                
        except Exception as e:
            system_logger.exception(f'批量发送消息过程中发生严重错误：{e}')
    
    def update_message_status(self, ids):
        """更新消息状态到数据库"""
        max_batch_size = 1000  # 防止SQL语句过长
        for i in range(0, len(ids), max_batch_size):
            batch_ids = ids[i:i+max_batch_size]
            mongo_query = {"id": {"$in": batch_ids}}
            self.collection.update_many(mongo_query, {"$set": {"state": 3}})
    
    def handle_update_failure(self, ids):
        """处理状态更新失败的情况"""
        # 可以实现将失败ID记录到日志文件或专门的错误表
        system_logger.error(f'以下ID数据库状态更新失败：{ids}')
        with open('.\log\failed_status_updates.txt', 'a', encoding='utf-8') as f:
            f.write(','.join([str(id) for id in ids]) + '\n')

    def whether_next_round(self, round: int):
        # 检查是否需要切换到下一轮
        remaining_daily_task_nums = """SELECT top 1 * FROM [RReportTask].[dbo].[CT_QianShuiGongGaoCompanyInfo] WHERE """\
                    """(state=0 or state=3 or state=-1 or state=101)"""
        remaining_daily_task_nums: list = self.db.sql_exec(remaining_daily_task_nums)
        if len(remaining_daily_task_nums) == 0:
            system_logger.info('没有状态为(0, 3, -1, 101)的数据，更新所有数据状态为0，进入下一轮')
            update_all_remaining_daily_task = """UPDATE [RReportTask].[dbo].[CT_QianShuiGongGaoCompanyInfo] SET state=0"""
            self.db.sql_exec(update_all_remaining_daily_task)
    
    def get_data_from_db(self):
        # sql_select = f"""SELECT top {self.sql_select_count} * FROM [RReportTask].[dbo].[CT_QianShuiGongGaoCompanyInfo] WHERE """\
        #         f"""(state=0 or state=-1) """\
        #         f"""order by priority desc, id asc"""
        mongo_query = {"state": {"$in": [0, -1]}}
        mongo_result = self.collection.find(mongo_query).limit(self.sql_select_count) # Cursor
        mongo_result = mongo_result.to_list(length=self.sql_select_count)
        print(mongo_result)
        system_logger.info(f'从数据库获取状态为(0, -1)的数据，{len(mongo_result)}条')
        return mongo_result
    
    def run(self):
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        while True:
            try:
                # self.whether_next_round(round)
                sql_result = self.get_data_from_db()
                
                if not sql_result:
                    consecutive_failures = 0  # 重置失败计数
                    time.sleep(self.sql_select_frenquency)
                    continue
                
                self.send_to_queue(sql_result)
                consecutive_failures = 0  # 重置失败计数
                
            except Exception as e:
                consecutive_failures += 1
                system_logger.exception(f'调度器主循环异常：{e}')
                
                # 根据连续失败次数调整等待时间
                wait_time = min(self.sql_select_frenquency * consecutive_failures, 300)  # 最大等待5分钟
                system_logger.info(f'等待{wait_time}秒后重试...')
                
                # 如果连续失败次数过多，尝试重建资源
                if consecutive_failures >= max_consecutive_failures:
                    system_logger.warning(f'连续失败{consecutive_failures}次，尝试重建数据库连接和RabbitMQ连接...')
                    try:
                        # self.mongodb.disconnect()
                        # self.rabbit.reset_connection()
                        self.env_init()
                        consecutive_failures = 0
                    except Exception as init_error:
                        system_logger.error(f'重建资源失败：{init_error}')
                
                time.sleep(wait_time)

            time.sleep(self.sql_select_frenquency)

if __name__ == "__main__":
    scheduler = Scheduler()
    scheduler.run()