import enum
import os


class Properties:
    sqlite_db_path = os.path.join(os.path.dirname(__file__), 'RunQueue.db')
    cost_tracker_sqlite_db = os.path.join(os.path.dirname(__file__), 'CostTracker.db')


class RunStates(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"
    INITIATED = "INITIATED"


class CloudType(enum.Enum):
    aws = "aws"
    azure = "azure"
    gcp = "gcp"
