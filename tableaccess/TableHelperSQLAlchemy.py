import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.pool import SingletonThreadPool

from tableaccess.properties import Properties, RunStates
from tableobjects.TESTRUN import TESTRUNS
from tableobjects.meta_base import ModelBase


class SQLAlchemyTableHelper:
    def __init__(self):
        sql_conn_path = f'sqlite:///{Properties.sqlite_db_path}'
        engine = sqlalchemy.create_engine(sql_conn_path, echo=False, poolclass=SingletonThreadPool)
        ModelBase.metadata.create_all(engine)
        factory = orm.sessionmaker()
        factory.configure(bind=engine)
        self.factory = factory

    def all_runs(self):
        session = self.factory()
        runs = session.query(TESTRUNS).order_by(TESTRUNS.run_id).all()
        session.close()
        return [run.to_json() for run in list(runs)]

    def create_table(self):
        pass

    def next_eligible_run(self):
        pending_runs = self.pending_runs()
        if not pending_runs:
            return None
        return pending_runs[0]['run_id']

    def pending_runs(self):
        session = self.factory()
        runs = session.query(TESTRUNS).filter(TESTRUNS.run_state == RunStates.PENDING.value).order_by(
            TESTRUNS.run_id).all()
        session.close()
        return [run.to_json() for run in list(runs)]

    def running_runs(self):
        session = self.factory()
        runs = session.query(TESTRUNS).filter(TESTRUNS.run_state == RunStates.RUNNING.value).order_by(
            TESTRUNS.run_id).all()
        session.close()
        return [run.to_json() for run in list(runs)]

    def failed_runs(self):
        session = self.factory()
        runs = session.query(TESTRUNS).filter(TESTRUNS.run_state == RunStates.FAILED.value).order_by(
            TESTRUNS.run_id).all()
        session.close()
        return [run.to_json() for run in list(runs)]

    def successful_runs(self):
        session = self.factory()
        runs = session.query(TESTRUNS).filter(TESTRUNS.run_state == RunStates.SUCCESS.value).order_by(
            TESTRUNS.run_id).all()
        session.close()
        return [run.to_json() for run in list(runs)]

    def initiated_runs(self):
        session = self.factory()
        runs = session.query(TESTRUNS).filter(TESTRUNS.run_state == RunStates.INITIATED.value).order_by(
            TESTRUNS.run_id).all()
        session.close()
        return [run.to_json() for run in list(runs)]

    def update_run_state(self, run_id, run_state):
        session = self.factory()
        session.query(TESTRUNS).filter(TESTRUNS.run_id == run_id).update({TESTRUNS.run_state: run_state})
        session.commit()
        session.close()

    def delete_run_from_queue(self, run_id):
        session = self.factory()
        session.query(TESTRUNS).filter(TESTRUNS.run_id == run_id).delete()
        session.commit()
        session.close()

    @property
    def queue(self):
        return self.pending_runs()

    def add_run_to_queue(self, run_name):
        session = self.factory()
        test_run = TESTRUNS()
        test_run.run_name = run_name
        test_run.run_state = RunStates.PENDING.value
        session.add(test_run)
        session.commit()
        run_id = test_run.run_id
        session.close()
        return run_id


if __name__ == '__main__':
    t = SQLAlchemyTableHelper()
    t.add_run_to_queue('test2')
    t.add_run_to_queue('test3')
