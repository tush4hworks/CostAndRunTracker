import random
import threading
import time
from multiprocessing import Process

from common.custom_logging import CustomLogger
from tableaccess.AccessFactory import AccessFactory
from tableaccess.properties import RunStates

table_helper = AccessFactory.get_db_conn_service()

logger = CustomLogger.getLogger(__name__)


def finish_run(to_run):
    """
    Finish Run
    :param to_run:
    :return:
    """
    time.sleep(random.choice(4, 7))
    logger.info(f'Starting run {to_run}')
    table_helper.update_run_state(to_run, RunStates.RUNNING.value)
    time.sleep(random.choice(range(5, 10)))
    logger.info(f'Finished run {to_run}')
    table_helper.update_run_state(to_run, random.choice([RunStates.SUCCESS.value, RunStates.FAILED.value]))
    return RunStates.SUCCESS.value


def execute_run(to_run):
    result = threading.Thread(target=finish_run, args=[to_run])
    result.start()


def program_loop(lock: threading.RLock):
    while True:
        wait_until_resources_available()
        with lock:
            """
            Find next eligible run, if found transition it to INITIATED
            """
            next_run = table_helper.next_eligible_run()
            if next_run:
                table_helper.update_run_state(next_run, RunStates.INITIATED.value)
                execute_run(next_run)


def wait_until_resources_available():
    logger.info('Blocking until resource availability')
    time.sleep(random.choice(range(2, 15)))
    logger.info('Resources available now')


class TriggerRun:
    @staticmethod
    def trigger_runs():
        lock = threading.RLock()
        p = Process(target=program_loop, args=[lock])
        p.start()


if __name__ == '__main__':
    TriggerRun.trigger_runs()
    time.sleep(100)
