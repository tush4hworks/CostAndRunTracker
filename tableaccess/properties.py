import enum
import os


class Properties:
    sqlite_db_path = os.path.join(os.path.dirname(__file__), 'RunQueue.db')


class RunStates(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"
    INITIATED = "INITIATED"
