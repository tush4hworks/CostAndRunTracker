import sqlalchemy

from tableobjects.meta_base import ModelBase


class TESTRUNS(ModelBase):
    __tablename__ = 'TESTRUNS'

    run_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    run_name = sqlalchemy.Column(sqlalchemy.String)
    run_state = sqlalchemy.Column(sqlalchemy.String)

    def to_json(self):
        return {
            'run_id': self.run_id,
            'run_name': self.run_name,
            'run_state': self.run_state
        }
