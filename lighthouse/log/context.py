import logging


class ContextFilter(logging.Filter):
    """
    Simple `logging.Filter` subclass that adds a `program` attribute to
    each `LogRecord`.

    The attribute's value comes from the "program" class attribute.
    """

    program = None

    def filter(self, record):
        """
        Sets the `program` attribute on the record.  Always returns `True` as
        we're not actually filtering any records, just enhancing them.
        """
        record.program = self.program
        return True
