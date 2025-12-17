import os
import sys
import logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.dspider import common
from dspider.common.mongodb_service import mongodb_conn, MongoDBConnection, mongodb_config
from dspider.common.rabbitmq_service import rabbitmq_client, RabbitMQClient
from dspider.common.minio_service import minio_client



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)