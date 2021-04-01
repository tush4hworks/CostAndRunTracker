import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, make_response, jsonify, request
from flask_cors import CORS

from runlogic.CostTracker import ProcessTracker
from tableaccess.AccessFactory import AccessFactory

cost_app = Flask(__name__)

CORS(cost_app)

table_helper = AccessFactory.get_cost_by_time_db_conn()

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = RotatingFileHandler(filename='logs/flask.log', maxBytes=1000000, backupCount=5)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
cost_app.logger.addHandler(file_handler)
cost_app.logger.setLevel(logging.DEBUG)


@cost_app.route("/index", methods=["GET"])
def index():
    return make_response(jsonify({"message": "Welcome to E2E COST BY TIME TRACKER"}))


@cost_app.route("/api/v1/service", methods=["GET"])
def get_latest_for_all_services():
    try:
        cost_app.logger.info('Getting latest consumption for all services')
        data = table_helper.latest_consumption_of_all_services()
        return make_response(jsonify(data))
    except Exception as e:
        cost_app.logger.exception(e)
        return make_response(jsonify({'Exception': e.__repr__()}), 400)


@cost_app.route("/api/v1/tag", methods=["GET"])
def get_latest_for_all_tags():
    try:
        cost_app.logger.info('Getting latest consumption for all tags')
        data = table_helper.latest_consumption_of_all_tags()
        return make_response(jsonify(data))
    except Exception as e:
        cost_app.logger.exception(e)
        return make_response(jsonify({'Exception': e.__repr__()}), 400)


@cost_app.route("/api/v1/tag/<tag>", methods=["GET"])
def get_latest_by_tag(tag):
    try:
        cost_app.logger.info(f'Getting latest consumption for tag {tag}')
        data = table_helper.latest_consumption_by_tag(tag)
        return make_response(jsonify(data))
    except Exception as e:
        cost_app.logger.exception(e)
        return make_response(jsonify({'Exception': e.__repr__()}), 400)


@cost_app.route("/api/v1/service/<service>", methods=["GET"])
def get_latest_by_service(service):
    try:
        cost_app.logger.info(f'Getting latest consumption for service {service}')
        data = table_helper.latest_consumption_by_service(service)
        return make_response(jsonify(data))
    except Exception as e:
        cost_app.logger.exception(e)
        return make_response(jsonify({'Exception': e.__repr__()}), 400)


@cost_app.route("/api/v1/service/history", methods=["GET"])
def get_service_history():
    try:
        service_filter = request.args.get('service')
        hours = int(request.args.get('hours', 5))
        cost_app.logger.info(
            f'Getting service consumption history for {service_filter if service_filter else "all"} service(s)')
        data = table_helper.aggregate_by_service(n_hour_prior=hours, service=service_filter)
        return make_response(jsonify(data))
    except Exception as e:
        cost_app.logger.exception(e)
        return make_response(jsonify({'Exception': e.__repr__()}), 400)


@cost_app.route("/api/v1/tag/history", methods=["GET"])
def get_tag_history():
    try:
        tag_filter = request.args.get('tag')
        hours = int(request.args.get('hours', 5))
        cost_app.logger.info(
            f'Getting tag consumption history for {tag_filter if tag_filter else "all"} service(s)')
        data = table_helper.aggregate_by_tag(n_hour_prior=hours, tag=tag_filter)
        return make_response(jsonify(data))
    except Exception as e:
        cost_app.logger.exception(e)
        return make_response(jsonify({'Exception': e.__repr__()}), 400)


@cost_app.route("/api/v1/service/tag/history", methods=["GET"])
def get_service_and_tag_history():
    try:
        hours = int(request.args.get('hours', 5))
        cost_app.logger.info("Aggregating metrices for service and tags")
        data = table_helper.aggregate_by_service_and_tag(n_hour_prior=hours)
        return make_response(jsonify(data))
    except Exception as e:
        cost_app.logger.exception(e)
        return make_response(jsonify({'Exception': e.__repr__()}), 400)


if __name__ == '__main__':
    ProcessTracker.start()
    cost_app.run(host='0.0.0.0', port=5001, debug=True)
