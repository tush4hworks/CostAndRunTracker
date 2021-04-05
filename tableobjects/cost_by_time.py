import datetime

import sqlalchemy

from tableaccess.properties import CloudType
from tableobjects.meta_base import ModelBase


class cost_by_time(ModelBase):
    __tablename__ = 'COST_BY_TIME'
    SN = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    cloud_type = sqlalchemy.Column(sqlalchemy.Enum(CloudType))
    tag = sqlalchemy.Column(sqlalchemy.String)
    service = sqlalchemy.Column(sqlalchemy.String)
    cost_per_hour = sqlalchemy.Column(sqlalchemy.INT)

    def to_json(self):
        return {
            'SN': self.SN,
            'timestamp': datetime.datetime.strftime(self.timestamp, '%Y-%m-%d %H:%M:%S'),
            'tag': self.tag,
            'service': self.service,
            'cost_per_hour': self.cost_per_hour
        }
