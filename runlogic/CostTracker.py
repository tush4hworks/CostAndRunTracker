import datetime
import random
import time
from multiprocessing import Process

from common.custom_logging import CustomLogger
from tableaccess.AccessFactory import AccessFactory

table_helper = AccessFactory.get_cost_by_time_db_conn()

logger = CustomLogger.getLogger(__name__)


def consumption_poller():
    services = ["EC2", "CloudFormation", "EBS", "EKS"]
    tags = ["DMX", "DFX", "DWX", "MLX"]
    while True:
        logger.info('Starting consumption collection')
        timestamp = datetime.datetime.now()

        tag = random.choice(tags)
        service = random.choice(services)
        cost = random.choice(range(1000, 2500))
        logger.info(f'Adding record  {timestamp}|{service}|{tag}|{cost}')
        table_helper.add_row(cost=cost, service=service, tag=tag, timestamp=timestamp)

        tag = random.choice(tags)
        service = random.choice(services)
        cost = random.choice(range(1000, 2500))
        logger.info(f'Adding record  {timestamp}|{service}|{tag}|{cost}')
        table_helper.add_row(cost=cost, service=service, tag=tag, timestamp=timestamp)

        logger.info('Sleeping for 2 minutes')
        time.sleep(120)


class ProcessTracker:
    @staticmethod
    def start():
        p = Process(target=consumption_poller, args=[])
        p.start()
