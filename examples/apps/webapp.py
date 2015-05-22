#!/usr/bin/env/ python2.7
import argparse
import logging

from flask import Flask, abort
import redis


app = Flask(__name__)
logger = logging.getLogger(__name__)


REDIS_PORT = 9999


@app.route('/')
def hello_world():
    conn = redis.Redis("127.0.0.1", port=REDIS_PORT)

    count = conn.incr("webapp:counter")

    return "<h1>Current count: %d</h1>\n" % count


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
