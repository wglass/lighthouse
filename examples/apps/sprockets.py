#!/usr/bin/env/ python2.7
import argparse
import logging
import json

from flask import Flask, abort, jsonify, request
import redis
import requests


app = Flask(__name__)
logger = logging.getLogger(__name__)


REDIS_PORT = 9999
PARTNER_PORT = 7777


def get_token():
    partner_response = requests.get("http://localhost:%d/token" % PARTNER_PORT)

    return json.loads(partner_response.text)["token"]


@app.route('/api/sprockets')
def get_sprockets():
    conn = redis.Redis("127.0.0.1", port=REDIS_PORT)

    sprockets = conn.smembers("sprockets")

    return jsonify(token=get_token(), sprockets=list(sprockets))


@app.route('/api/sprockets', methods=["POST"])
def create_sprocket():
    conn = redis.Redis("127.0.0.1", port=REDIS_PORT)

    if "sprocket" not in request.form or not request.form["sprocket"]:
        abort(400)

    conn.sadd("sprockets", request.form["sprocket"])

    return jsonify(token=get_token(), success=True)


@app.route("/health")
def healthcheck():
    conn = redis.Redis("127.0.0.1", port=REDIS_PORT)

    try:
        redis_passed = conn.ping()
    except Exception:
        logger.exception("Error pinging redis service!")
        redis_passed = False

    if not redis_passed:
        logger.warn("redis unavailable!")
        abort(503)

    response = requests.get("http://localhost:%d/status" % PARTNER_PORT)

    if response.status_code != 200:
        logger.warn("partner response: %d", response.status_code)
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
