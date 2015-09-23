import logging

from .context import ContextFilter


def setup(program):
    """
    Simple function that sets the program on the ContextFilter and returns
    the root logger.
    """
    ContextFilter.program = program

    return logging.getLogger()
