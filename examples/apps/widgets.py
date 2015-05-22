#!/usr/bin/env/ python2.7
import argparse
import logging

from flask import Flask, abort, jsonify, request
import redis


app = Flask(__name__)
logger = logging.getLogger(__name__)


REDIS_PORT = 9999


@app.route('/api/widgets')
def get_widgets():
    conn = redis.Redis("127.0.0.1", port=REDIS_PORT)

    widgets = conn.hgetall("widgets")

    return jsonify(widgets=widgets)


@app.route('/api/widgets', methods=["POST"])
def create_widget():
    conn = redis.Redis("127.0.0.1", port=REDIS_PORT)

    if "widget" not in request.form or not request.form["widget"]:
        abort(400)

    conn.hincrby("widgets", request.form["widget"], 1)

    return jsonify(success=True)


@app.route("/health")
def healthcheck():
    conn = redis.Redis("127.0.0.1", port=REDIS_PORT)

    try:
        passed = conn.ping()
    except Exception:
        logger.exception("Error pinging redis service!")
        passed = False

    if not passed:
        abort(503)

    return "a-ok!"


parser = argparse.ArgumentParser(description="Toy web server.")
parser.add_argument(
    "port", type=int, default=8888,
    help="Port to listen on."
)


if __name__ == '__main__':
    args = parser.parse_args()

    app.run(host="0.0.0.0", port=args.port, debug=True)
