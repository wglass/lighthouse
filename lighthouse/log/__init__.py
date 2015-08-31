import logging

from .cli import CLIHandler
from .context import ContextFilter
from .config import load_yaml, load_json, load_ini


def setup(program, config_file=None):
    """
    Simple function that attaches the CLIHandler to the root logger.
    """
    if not config_file:
        logger = logging.getLogger()
        logger.addHandler(CLIHandler())
        return logger

    if config_file.endswith(".yaml") or config_file.endswith(".yml"):
        load_yaml(config_file)
    elif config_file.endswith(".json"):
        load_json(config_file)
    else:
        load_ini(config_file)

    ContextFilter.program = program

    return logging.getLogger()
