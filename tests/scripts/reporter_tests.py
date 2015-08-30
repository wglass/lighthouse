import logging
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from lighthouse.scripts import reporter


@patch("lighthouse.scripts.reporter.reporter.Reporter")
@patch("lighthouse.scripts.reporter.parser")
class ReporterScriptTests(unittest.TestCase):

    def test_run_handles_keyboardinterrupt(self, parser, Reporter):
        parser.parse_args.return_value.log_config = None
        Reporter.return_value.start.side_effect = KeyboardInterrupt

        reporter.run()

        Reporter.return_value.stop.assert_called_once_with()

    @patch("lighthouse.scripts.reporter.log")
    def test_debug_flag_set(self, log, parser, Reporter):
        logger = log.setup.return_value

        parser.parse_args.return_value.debug = True

        reporter.run()

        logger.setLevel.assert_called_once_with(logging.DEBUG)

    @patch("lighthouse.scripts.reporter.log")
    def test_debug_flag_not_set(self, log, parser, Reporter):
        logger = log.setup.return_value

        parser.parse_args.return_value.debug = False

        reporter.run()

        logger.setLevel.assert_called_once_with(logging.INFO)
