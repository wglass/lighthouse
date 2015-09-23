try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from lighthouse import log


class LogTests(unittest.TestCase):

    @patch("lighthouse.log.logging")
    def test_setup_returns_root_logger(self, mock_logging):
        result = log.setup("foobar")

        self.assertEqual(result, mock_logging.getLogger.return_value)

        mock_logging.getLogger.assert_called_once_with()

    @patch("lighthouse.log.ContextFilter")
    def test_setup_sets_context_filter_program(self, ContextFilter):
        log.setup("foobar")

        self.assertEqual(ContextFilter.program, "foobar")
