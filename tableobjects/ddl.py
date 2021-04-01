create_table = """CREATE TABLE IF NOT EXISTS TESTRUNS (
   run_id INTEGER PRIMARY KEY AUTOINCREMENT,
   run_name text NOT NULL,
   run_state text NOT NULL
);"""

insert_row = """INSERT INTO TESTRUNS (run_name, run_state)  values(?,?);"""

runs_in_state = """SELECT * FROM TESTRUNS WHERE RUN_STATE == ?;"""

update_run_status = """UPDATE TESTRUNS SET RUN_STATE == ? WHERE RUN_ID == ?;"""

all_runs = """SELECT * FROM TESTRUNS"""

last_insert_rowid = """SELECT last_insert_rowid();"""