import datetime
from collections import namedtuple

import sqlalchemy
from sqlalchemy import orm, func

from tableaccess.properties import Properties, CloudType
from tableobjects.cost_by_time import cost_by_time
from tableobjects.meta_base import ModelBase

tag_and_service_agg = namedtuple('tag_and_service_agg', ['timestamp', 'service', 'tag', 'cost_per_hour'])
service_agg = namedtuple('service_agg', ['timestamp', 'service', 'cost_per_hour'])
tag_agg = namedtuple('tag_agg', ['timestamp', 'tag', 'cost_per_hour'])
tag_total = namedtuple('tag_total', ['tag', 'total_cost'])
service_total = namedtuple('service_total', ['service', 'total_cost'])


class CbyTSQLAlchemyTableHelper:
    def __init__(self):
        sql_conn_path = f'sqlite:///{Properties.cost_tracker_sqlite_db}'
        engine = sqlalchemy.create_engine(sql_conn_path, echo=False)
        ModelBase.metadata.create_all(engine)
        factory = orm.sessionmaker()
        factory.configure(bind=engine)
        self.factory = factory

    def _effective_time_window(self, n_hour_prior):
        """
        Normalized effective time
        Just subtracting timedelta may lead to lose out some records that belong to the same hour but are earlier than
        exact time. We will always look from 0th minute of the hour
        i.e. if current time is 6:30, and we want last 5 hour data
        we will start looking from 1:00 instead of 1:30
        :param n_hour_prior:
        :return:
        """
        exact_from = datetime.datetime.now() - datetime.timedelta(hours=n_hour_prior)
        normalized_from = exact_from - datetime.timedelta(seconds=exact_from.minute * 60)
        return normalized_from

    def add_row(self, cloud_type: CloudType, cost, service, tag="TestDevelopment", timestamp=None):
        """
        INSERT INTO "COST_BY_TIME" (timestamp, tag, service, cost_per_hour) VALUES (?, ?, ?, ?)
        :param cloud_type:
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
        c.cloud_type = cloud_type
        c.cost_per_hour = cost
        c.service = service
        c.tag = tag
        session.add(c)
        session.commit()
        session.close()

    def latest_consumption_by_service(self, cloud_type: CloudType, service):
        """
        Returns latest consumption for a service
        Cost for all tags with the same service name are summed if they are for the same timestamp
        :param cloud_type
        :param service:
        :return:
        """
        session = self.factory()
        obj = session.query(cost_by_time).filter(cost_by_time.cloud_type == cloud_type).filter(
            cost_by_time.service == service).order_by(
            cost_by_time.timestamp.desc()).first()
        if not obj:
            return []
        latest_timestamp = obj.timestamp

        agg = session.query(cost_by_time).filter(cost_by_time.cloud_type == cloud_type).filter(
            cost_by_time.service == service).filter(
            cost_by_time.timestamp == latest_timestamp).with_entities(
            func.strftime('%Y-%m-%d %H:%M:%S', cost_by_time.timestamp), cost_by_time.service,
            func.sum(cost_by_time.cost_per_hour)).first()
        session.close()
        return service_agg(*agg)._asdict()

    def latest_consumption_of_all_services(self, cloud_type: CloudType):
        """
        Latest consumption of all services
        :param cloud_type
        :return:
        """
        return_list = []
        session = self.factory()
        objs = session.query(cost_by_time.service).distinct().all()
        session.close()
        for service in (item[0] for item in objs):
            consumption = self.latest_consumption_by_service(cloud_type, service)
            if consumption:
                return_list.append(consumption)
        return sorted(return_list, key=lambda x: x['timestamp'], reverse=True)

    def latest_consumption_by_tag(self, cloud_type: CloudType, tag):
        """
        Returns latest consumption for a tag
        Cost for all services with the same tag name are summed if they are for the same timestamp
        :param cloud_type
        :param tag:
        :return:
        """
        session = self.factory()
        obj = session.query(cost_by_time).filter(cost_by_time.cloud_type == cloud_type).filter(
            cost_by_time.tag == tag).order_by(
            cost_by_time.timestamp.desc()).first()
        if not obj:
            return []
        latest_timestamp = obj.timestamp
        session.close()

        session = self.factory()
        agg = session.query(cost_by_time).filter(cost_by_time.cloud_type == cloud_type).filter(
            cost_by_time.tag == tag).filter(
            cost_by_time.timestamp == latest_timestamp).with_entities(
            func.strftime('%Y-%m-%d %H:%M:%S', cost_by_time.timestamp), cost_by_time.tag,
            func.sum(cost_by_time.cost_per_hour)).first()
        session.close()
        return tag_agg(*agg)._asdict()

    def latest_consumption_of_all_tags(self, cloud_type: CloudType):
        """
        Latest consumption of all tags
        :param cloud_type
        :return:
        """
        return_list = []
        session = self.factory()
        objs = session.query(cost_by_time.tag).distinct().all()
        session.close()
        for tag in (item[0] for item in objs):
            consumption = self.latest_consumption_by_tag(cloud_type, tag)
            if consumption:
                return_list.append(consumption)
        return sorted(return_list, key=lambda x: x['timestamp'], reverse=True)

    def aggregate_by_service_and_tag(self, cloud_type: CloudType, n_hour_prior=5):
        """
        Aggregate by service and tag per hour
        Group record by service, tag and hour -> output average cost
        :param n_hour_prior:
        :return:
        """
        session = self.factory()
        objs = session.query(cost_by_time).filter(cost_by_time.cloud_type == cloud_type).filter(
            cost_by_time.timestamp > self._effective_time_window(n_hour_prior)).with_entities(
            func.strftime('%Y-%m-%d %H', cost_by_time.timestamp),
            cost_by_time.service, cost_by_time.tag,
            func.avg(cost_by_time.cost_per_hour)).group_by(
            cost_by_time.service, cost_by_time.tag,
            func.strftime('%Y-%m-%d %H', cost_by_time.timestamp)).order_by(
            cost_by_time.timestamp.desc()).all()
        session.close()
        return [tag_and_service_agg(*obj)._asdict() for obj in objs]

    def aggregate_by_service(self, cloud_type: CloudType, n_hour_prior=5, service=None):
        """
        Aggregate by service per hour
        Do subqueries because records with the same timestamp(minute precision) and service need to be summed before averaging them
        Query 1-> Group record by service, timestamp (minute precision)
                    (assume we have a minute precision betweeen successive polls) -> sum(cost)
        Query 2-> Group query 1 by timestamp (hour precision) -> avg(cost)
        :param cloud_type
        :param n_hour_prior:
        :param service: optional
        :return:
        """
        session = self.factory()
        in_time_window = session.query(cost_by_time).filter(cost_by_time.cloud_type == cloud_type).filter(
            cost_by_time.timestamp > self._effective_time_window(n_hour_prior))
        if service:
            in_time_window = in_time_window.filter(
                cost_by_time.service == service)

        # Query1
        summation_over_same_timestamp = in_time_window.with_entities(
            func.strftime('%Y-%m-%d %H:%M', cost_by_time.timestamp).label('time_minute'),
            cost_by_time.service.label('service'),
            func.sum(cost_by_time.cost_per_hour).label('cost_across_tags')).group_by(
            cost_by_time.service, 'time_minute').subquery()

        session.close()

        session = self.factory()
        # Query2
        objs = session.query(func.strftime('%Y-%m-%d %H', summation_over_same_timestamp.c.time_minute),
                             summation_over_same_timestamp.c.service,
                             func.avg(summation_over_same_timestamp.c.cost_across_tags)).group_by(
            func.strftime('%Y-%m-%d %H', summation_over_same_timestamp.c.time_minute),
            summation_over_same_timestamp.c.service).order_by(
            summation_over_same_timestamp.c.time_minute.desc()).all()
        session.close()

        return [(service_agg(*obj)._asdict()) for obj in objs]

    def aggregate_by_tag(self, cloud_type: CloudType, n_hour_prior=5, tag=None):
        """
        Aggregate by tag per hour
        Do subqueries because records with the same timestamp(minute precision) and tag need to be summed before averaging them
        Query 1-> Group record by tag, timestamp (minute precision)
                    (assume we have a minute precision betweeen successive polls) -> sum(cost)
        Query 2-> Group query 1 by timestamp (hour precision) -> avg(cost)
        :param cloud_type
        :param n_hour_prior:
        :param tag: optional
        :return:
        """
        session = self.factory()
        in_time_window = session.query(cost_by_time).filter(cost_by_time.cloud_type == cloud_type).filter(
            cost_by_time.timestamp > self._effective_time_window(n_hour_prior))
        if tag:
            in_time_window = in_time_window.filter(
                cost_by_time.tag == tag)

        # Query1
        summation_over_same_timestamp = in_time_window.with_entities(
            func.strftime('%Y-%m-%d %H:%M', cost_by_time.timestamp).label('time_minute'),
            cost_by_time.tag.label('tag'),
            func.sum(cost_by_time.cost_per_hour).label('cost_across_services')).group_by(
            cost_by_time.tag, 'time_minute').subquery()

        session.close()

        session = self.factory()
        # Query2
        objs = session.query(func.strftime('%Y-%m-%d %H', summation_over_same_timestamp.c.time_minute),
                             summation_over_same_timestamp.c.tag,
                             func.avg(summation_over_same_timestamp.c.cost_across_services)).group_by(
            func.strftime('%Y-%m-%d %H', summation_over_same_timestamp.c.time_minute),
            summation_over_same_timestamp.c.tag).order_by(
            summation_over_same_timestamp.c.time_minute.desc()).all()
        session.close()
        return [(tag_agg(*obj)._asdict()) for obj in objs]

    def total_cost_by_tag(self, cloud_type: CloudType, n_hour_prior=5, tag=None):
        """
        Estimated total cost by tag
        :param cloud_type:
        :param n_hour_prior:
        :param tag:
        :return:
        """
        return_list = []
        per_hour_costs = self.aggregate_by_tag(cloud_type, n_hour_prior, tag)
        tags = set([item['tag'] for item in per_hour_costs])
        for tag in tags:
            total_cost_by_tag = sum(item['cost_per_hour'] for item in filter(lambda x: x['tag'] == tag, per_hour_costs))
            return_list.append(tag_total(tag, total_cost_by_tag)._asdict())
        return return_list

    def total_cost_by_service(self, cloud_type: CloudType, n_hour_prior=5, service=None):
        """
        Estimated total cost by service
        :param cloud_type:
        :param n_hour_prior:
        :param service:
        :return:
        """
        return_list = []
        per_hour_costs = self.aggregate_by_service(cloud_type, n_hour_prior, service)
        services = set([item['service'] for item in per_hour_costs])
        for service in services:
            total_cost_by_service = sum(
                item['cost_per_hour'] for item in filter(lambda x: x['service'] == service, per_hour_costs))
            return_list.append(service_total(service, total_cost_by_service)._asdict())
        return return_list


if __name__ == '__main__':
    cbyt = CbyTSQLAlchemyTableHelper()
    # cbyt.add_row(cloud_type=CloudType.azure, cost=2100, service='DFX', tag='XX', timestamp=datetime.datetime.now())
    print(cbyt.aggregate_by_service(cloud_type=CloudType.aws, n_hour_prior=10, service='CloudFormation'))
    print(cbyt.total_cost_by_service(cloud_type=CloudType.aws, n_hour_prior=10))
