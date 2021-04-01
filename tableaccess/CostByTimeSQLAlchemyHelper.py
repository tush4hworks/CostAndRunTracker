import datetime
from collections import namedtuple

import sqlalchemy
from sqlalchemy import orm, func

from tableaccess.properties import Properties
from tableobjects.cost_by_time import cost_by_time
from tableobjects.meta_base import ModelBase

tag_and_service_agg = namedtuple('tag_and_service_agg', ['timestamp', 'service', 'tag', 'cost_per_hour'])
service_agg = namedtuple('service_agg', ['timestamp', 'service', 'cost_per_hour'])
tag_agg = namedtuple('tag_agg', ['timestamp', 'tag', 'cost_per_hour'])


class CbyTSQLAlchemyTableHelper:
    def __init__(self):
        sql_conn_path = f'sqlite:///{Properties.sqlite_db_path}'
        engine = sqlalchemy.create_engine(sql_conn_path, echo=False)
        ModelBase.metadata.create_all(engine)
        factory = orm.sessionmaker()
        factory.configure(bind=engine)
        self.factory = factory

    def add_row(self, cost, service, tag="TestDevelopment", timestamp=None):
        """
        INSERT INTO "COST_BY_TIME" (timestamp, tag, service, cost_per_hour) VALUES (?, ?, ?, ?)
        :param cost:
        :param service:
        :param tag:
        :param timestamp:
        :return:
        """
        session = self.factory()
        if not timestamp:
            timestamp = datetime.datetime.now()
        c = cost_by_time()
        c.timestamp = timestamp
        c.cost_per_hour = cost
        c.service = service
        c.tag = tag
        session.add(c)
        session.commit()
        session.close()

    def latest_consumption_by_service(self, service):
        """
        Latest consumption filtered by service
        SELECT strftime(?, "COST_BY_TIME".timestamp) AS strftime_1, "COST_BY_TIME".service AS "COST_BY_TIME_service",
        avg("COST_BY_TIME".cost_per_hour) AS avg_1
        FROM "COST_BY_TIME"
        WHERE "COST_BY_TIME".service = ? AND "COST_BY_TIME".timestamp = ?
        LIMIT ? OFFSET ?
        :param service:
        :return:
        """
        session = self.factory()
        obj = session.query(cost_by_time).filter(cost_by_time.service == service).order_by(
            cost_by_time.timestamp.desc()).first()
        if not obj:
            return []
        latest_timestamp = obj.timestamp
        session.close()
        # Closing and re-opening otherwise SQLAlchemy throws warnings that SQLite objects can't be shared b/w threads
        session = self.factory()
        agg = session.query(cost_by_time).filter(cost_by_time.service == service).filter(
            cost_by_time.timestamp == latest_timestamp).with_entities(
            func.strftime('%Y-%m-%d %H:%M:%S', cost_by_time.timestamp), cost_by_time.service,
            func.avg(cost_by_time.cost_per_hour)).first()
        session.close()
        return service_agg(*agg)._asdict()

    def latest_consumption_of_all_services(self):
        """
        Latest consumption of all services
        :return:
        """
        return_list = []
        session = self.factory()
        objs = session.query(cost_by_time.service).distinct().all()
        session.close()
        for service in (item[0] for item in objs):
            consumption = self.latest_consumption_by_service(service)
            if consumption:
                return_list.append(consumption)
        return sorted(return_list, key=lambda x: x['timestamp'], reverse=True)

    def latest_consumption_by_tag(self, tag):
        """
        Latest consumption filtered by tag
        SELECT strftime(?, "COST_BY_TIME".timestamp) AS strftime_1, "COST_BY_TIME".tag AS "COST_BY_TIME_tag",
        avg("COST_BY_TIME".cost_per_hour) AS avg_1
        FROM "COST_BY_TIME"
        WHERE "COST_BY_TIME".tag = ? AND "COST_BY_TIME".timestamp = ?
        LIMIT ? OFFSET ?
        :param tag:
        :return:
        """
        session = self.factory()
        obj = session.query(cost_by_time).filter(cost_by_time.tag == tag).order_by(
            cost_by_time.timestamp.desc()).first()
        if not obj:
            return []
        latest_timestamp = obj.timestamp
        session.close()

        session = self.factory()
        agg = session.query(cost_by_time).filter(cost_by_time.tag == tag).filter(
            cost_by_time.timestamp == latest_timestamp).with_entities(
            func.strftime('%Y-%m-%d %H:%M:%S', cost_by_time.timestamp), cost_by_time.tag,
            func.avg(cost_by_time.cost_per_hour)).first()
        session.close()
        return tag_agg(*agg)._asdict()

    def latest_consumption_of_all_tags(self):
        """
        Lastest consumption of all tags
        :return:
        """
        return_list = []
        session = self.factory()
        objs = session.query(cost_by_time.tag).distinct().all()
        session.close()
        for tag in (item[0] for item in objs):
            consumption = self.latest_consumption_by_tag(tag)
            if consumption:
                return_list.append(consumption)
        return sorted(return_list, key=lambda x: x['timestamp'], reverse=True)

    def aggregate_by_service_and_tag(self, n_hour_prior=5):
        """
        SELECT strftime(?, "COST_BY_TIME".timestamp) AS strftime_1, "COST_BY_TIME".service AS "COST_BY_TIME_service",
        "COST_BY_TIME".tag AS "COST_BY_TIME_tag", avg("COST_BY_TIME".cost_per_hour) AS avg_1
        FROM "COST_BY_TIME"
        WHERE "COST_BY_TIME".timestamp > ? GROUP BY "COST_BY_TIME".service, "COST_BY_TIME".tag, strftime(?,
        "COST_BY_TIME".timestamp) ORDER BY "COST_BY_TIME".timestamp DESC
        :param n_hour_prior:
        :return:
        """
        session = self.factory()
        objs = session.query(cost_by_time).filter(
            cost_by_time.timestamp > datetime.datetime.now() - datetime.timedelta(hours=n_hour_prior)).with_entities(
            func.strftime('%Y-%m-%d %H', cost_by_time.timestamp),
            cost_by_time.service, cost_by_time.tag,
            func.avg(cost_by_time.cost_per_hour)).group_by(
            cost_by_time.service, cost_by_time.tag,
            func.strftime('%Y-%m-%d %H', cost_by_time.timestamp)).order_by(
            cost_by_time.timestamp.desc()).all()
        session.close()
        return [tag_and_service_agg(*obj)._asdict() for obj in objs]

    def aggregate_by_service(self, n_hour_prior=5, service=None):
        """
        SELECT strftime(?, "COST_BY_TIME".timestamp) AS strftime_1, "COST_BY_TIME".service AS "COST_BY_TIME_service",
        avg("COST_BY_TIME".cost_per_hour) AS avg_1 FROM "COST_BY_TIME"
        WHERE "COST_BY_TIME".timestamp > ? GROUP BY "COST_BY_TIME".service, strftime(?, "COST_BY_TIME".timestamp)
        ORDER BY "COST_BY_TIME".timestamp DESC
        :param n_hour_prior:
        :param service: optional
        :return:
        """
        session = self.factory()
        in_time_window = session.query(cost_by_time).filter(
            cost_by_time.timestamp > datetime.datetime.now() - datetime.timedelta(hours=n_hour_prior))
        if service:
            in_time_window = in_time_window.filter(cost_by_time.service == service)
        objs = in_time_window.with_entities(
            func.strftime('%Y-%m-%d %H', cost_by_time.timestamp),
            cost_by_time.service,
            func.avg(cost_by_time.cost_per_hour)).group_by(
            cost_by_time.service,
            func.strftime('%Y-%m-%d %H', cost_by_time.timestamp)).order_by(
            cost_by_time.timestamp.desc()).all()
        session.close()
        return [service_agg(*obj)._asdict() for obj in objs]

    def aggregate_by_tag(self, n_hour_prior=5, tag=None):
        """
        SELECT strftime(?, "COST_BY_TIME".timestamp) AS strftime_1, "COST_BY_TIME".tag AS "COST_BY_TIME_tag",
        avg("COST_BY_TIME".cost_per_hour) AS avg_1
        FROM "COST_BY_TIME"
        WHERE "COST_BY_TIME".timestamp > ? GROUP BY "COST_BY_TIME".tag, strftime(?, "COST_BY_TIME".timestamp)
        ORDER BY "COST_BY_TIME".timestamp DESC
        :param n_hour_prior:
        :tag optional
        :return:
        """
        session = self.factory()
        in_time_window = session.query(cost_by_time).filter(
            cost_by_time.timestamp > datetime.datetime.now() - datetime.timedelta(hours=n_hour_prior))
        if tag:
            in_time_window = in_time_window.filter(cost_by_time.tag == tag)
        objs = in_time_window.with_entities(
            func.strftime('%Y-%m-%d %H', cost_by_time.timestamp),
            cost_by_time.tag,
            func.avg(cost_by_time.cost_per_hour)).group_by(
            cost_by_time.tag,
            func.strftime('%Y-%m-%d %H', cost_by_time.timestamp)).order_by(
            cost_by_time.timestamp.desc()).all()
        session.close()
        return [tag_agg(*obj)._asdict() for obj in objs]


if __name__ == '__main__':
    cbyt = CbyTSQLAlchemyTableHelper()
    cbyt.add_row(4000, service='XX', tag='DMX', timestamp=datetime.datetime.fromtimestamp(1617202664.747885))
    print(cbyt.latest_consumption_by_service(service="EC2"))
