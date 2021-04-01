import logging
import threading
from logging.handlers import RotatingFileHandler

from flask import Flask, request, make_response, jsonify
from flask_cors import CORS

from runlogic.TriggerRuns import TriggerRun
from tableaccess.AccessFactory import AccessFactory

app = Flask(__name__)

CORS(app)

rlock = threading.RLock()

table_helper = AccessFactory.get_db_conn_service()

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = RotatingFileHandler(filename='logs/flask.log', maxBytes=1000000, backupCount=5)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)


@app.route("/index", methods=["GET"])
def index():
    return make_response(jsonify({"message": "Welcome to E2E runs"}))


def validate_request(request: request):
    if not request.json or not all([request.json.get('run_name')]):
        raise Exception("Invalid Input:run_id is mandatory")
    return request.json


@app.route("/run", methods=["POST"])
def add_run():
    app.logger.info(f'Add run: {request}')
    with rlock:
        try:
            payload = validate_request(request)
            run_id = table_helper.add_run_to_queue(payload['run_name'])
            return make_response(jsonify({"run_id": run_id}))
        except Exception as e:
            return make_response(jsonify({"exception": e.__str__()}), 400)


@app.route("/runs/running", methods=["GET"])
def running_runs():
    return make_response(jsonify(table_helper.running_runs()))


@app.route("/runs/pending", methods=["GET"])
def pending_runs():
    return make_response(jsonify(table_helper.pending_runs()))


@app.route("/runs/failed", methods=["GET"])
def failed_runs():
    return make_response(jsonify(table_helper.failed_runs()))


@app.route("/runs/successful", methods=["GET"])
def successful_runs():
    return make_response(jsonify(table_helper.successful_runs()))


@app.route("/runs/initiated", methods=["GET"])
def initiated_runs():
    return make_response(jsonify(table_helper.initiated_runs()))


@app.route("/runs", methods=["GET"])
def all_runs():
    return make_response(jsonify(table_helper.all_runs()))


@app.route("/queue", methods=["GET"])
def current_queue():
    return make_response(jsonify({"queue": table_helper.queue}))


@app.route("/run/<run_id>", methods=["DELETE"])
def delete_run_from_queue(run_id):
    app.logger.info(f'Removing {run_id}')
    try:
        table_helper.delete_run_from_queue(run_id)
        return make_response(jsonify({"DELETED": True}))
    except Exception as e:
        return make_response(jsonify({"Exception": e.__str__()}), 500)


if __name__ == '__main__':
    TriggerRun.trigger_runs()
    app.run(host='0.0.0.0', port=5001, debug=True)
