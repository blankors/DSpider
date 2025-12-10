import os
import sys
import logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.dspider import common
from src.dspider.common.mongodb_client import mongodb_conn, MongoDBConnection, mongodb_config
from src.dspider.common.rabbitmq_client import rabbitmq_client, RabbitMQClient, rabbitmq_config
from src.dspider.common.minio_client import minio_client, MinioClient, minio_config



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)