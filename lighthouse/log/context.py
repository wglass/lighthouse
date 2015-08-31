import logging


class ContextFilter(logging.Filter):

    program = None

    def filter(self, record):
        record.program = self.program
        return True
