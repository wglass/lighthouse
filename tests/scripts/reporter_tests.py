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
        Reporter.return_value.start.side_effect = KeyboardInterrupt

        reporter.run()

        Reporter.return_value.stop.assert_called_once_with()

    @patch("lighthouse.scripts.reporter.log")
    def test_log_setup_called(self, log, parser, Reporter):
        reporter.run()

        log.setup.assert_called_once_with("REPORTER")
