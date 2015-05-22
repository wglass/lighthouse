import logging
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from lighthouse.scripts import writer


@patch("lighthouse.scripts.writer.writer.Writer")
@patch("lighthouse.scripts.writer.parser")
class WriterScriptTests(unittest.TestCase):

    def reset_log_handler(self):
        root_logger = logging.getLogger()

        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    def setUp(self):
        self.reset_log_handler()

    def tearDown(self):
        self.reset_log_handler()

    def test_run_handles_keyboardinterrupt(self, parser, Writer):
        Writer.return_value.start.side_effect = KeyboardInterrupt

        writer.run()

        Writer.return_value.stop.assert_called_once_with()

    @patch("lighthouse.scripts.writer.log")
    def test_debug_flag_set(self, log, parser, Writer):
        logger = log.setup.return_value

        parser.parse_args.return_value.debug = True

        writer.run()

        logger.setLevel.assert_called_once_with(logging.DEBUG)

    @patch("lighthouse.scripts.writer.log")
    def test_debug_flag_not_set(self, log, parser, Writer):
        logger = log.setup.return_value

        parser.parse_args.return_value.debug = False

        writer.run()

        logger.setLevel.assert_called_once_with(logging.INFO)
