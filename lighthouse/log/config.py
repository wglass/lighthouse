import json
import logging
import logging.config

import yaml


def load_yaml(filename):
    """
    Loads a logging config file in YAML.

    Treats the content of the YAML file as a dictConfig.
    """
    try:
        content = yaml.load(open(filename))
    except Exception:
        logging.exception("Error loading log config YAML file '%s'", filename)
        return

    logging.config.dictConfig(content)


def load_json(filename):
    """
    Loads a logging config file in JSON.

    Treats the content of the JSON file as a dictConfig.
    """
    try:
        content = json.load(open(filename))
    except Exception:
        logging.exception("Error loading log config JSON file '%s'", filename)
        return

    logging.config.dictConfig(content)


def load_ini(filename):
    """
    Loads a standard logging ini config file.
    """
    logging.config.fileConfig(filename)
