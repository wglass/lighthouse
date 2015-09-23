try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from lighthouse.scripts import writer


@patch("lighthouse.scripts.writer.writer.Writer")
@patch("lighthouse.scripts.writer.parser")
class WriterScriptTests(unittest.TestCase):

    def test_run_handles_keyboardinterrupt(self, parser, Writer):
        Writer.return_value.start.side_effect = KeyboardInterrupt

        writer.run()

        Writer.return_value.stop.assert_called_once_with()

    @patch("lighthouse.scripts.writer.log")
    def test_log_setup_called(self, log, parser, Writer):
        writer.run()

        log.setup.assert_called_once_with("WRITER")
