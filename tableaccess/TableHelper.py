import sqlite3
from collections import namedtuple

from tableaccess.properties import Properties, RunStates
from tableobjects.ddl import insert_row, create_table, runs_in_state, update_run_status, all_runs, last_insert_rowid

run_info = namedtuple("run_info", ["run_id", "run_name", "run_state"])


class TableHelper:
    def __init__(self):
        self.con = sqlite3.connect(Properties.sqlite_db_path)
        self.create_table()

    def create_table(self):
        cursor = self.con.cursor()
        cursor.execute(create_table)
        self.con.commit()
        cursor.close()

    def next_eligible_run(self):
        pending_runs = self.pending_runs()
        if not pending_runs:
            return None
        return pending_runs[0]['run_id']

    def pending_runs(self):
        cursor = self.con.cursor()
        cursor.execute(runs_in_state, (RunStates.PENDING.value,))
        ret_val = [run_info(*item)._asdict() for item in cursor.fetchall()]
        cursor.close()
        return ret_val

    def running_runs(self):
        cursor = self.con.cursor()
        cursor.execute(runs_in_state, (RunStates.RUNNING.value,))
        ret_val = [run_info(*item)._asdict() for item in cursor.fetchall()]
        cursor.close()
        return ret_val

    def failed_runs(self):
        cursor = self.con.cursor()
        cursor.execute(runs_in_state, (RunStates.FAILED.value,))
        ret_val = [run_info(*item)._asdict() for item in cursor.fetchall()]
        cursor.close()
        return ret_val

    def successful_runs(self):
        cursor = self.con.cursor()
        cursor.execute(runs_in_state, (RunStates.SUCCESS.value,))
        ret_val = [run_info(*item)._asdict() for item in cursor.fetchall()]
        cursor.close()
        return ret_val

    def update_run_state(self, run_id, run_state):
        cursor = self.con.cursor()
        cursor.execute(update_run_status, (run_state, run_id))
        self.con.commit()
        cursor.close()

    def all_runs(self):
        cursor = self.con.cursor()
        cursor.execute(all_runs)
        ret_val = [run_info(*item)._asdict() for item in cursor.fetchall()]
        cursor.close()
        return ret_val

    @property
    def queue(self):
        return self.pending_runs()

    def add_run_to_queue(self, run_name):
        cursor = self.con.cursor()
        cursor.execute(insert_row, (run_name, RunStates.PENDING.value))
        self.con.commit()
        cursor.execute(last_insert_rowid)
        run_id = cursor.fetchone()
        cursor.close()
        return run_id[0]


if __name__ == "__main__":
    print(TableHelper().add_run_to_queue('aws-1'))
