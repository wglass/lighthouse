import argparse
import logging
import uuid

from flask import Flask, jsonify


app = Flask(__name__)
logger = logging.getLogger(__name__)


@app.route('/token')
def generate_token():
    return jsonify(token=str(uuid.uuid4()))


@app.route("/status")
def healthcheck():
    return "OK"


parser = argparse.ArgumentParser(description="API token generator.")
parser.add_argument(
    "port", type=int, default=88,
    help="Port to listen on."
)


if __name__ == '__main__':
    args = parser.parse_args()

    app.run(host="0.0.0.0", port=args.port, debug=True)
