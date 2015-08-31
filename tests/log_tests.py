try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from lighthouse import log


class LogTests(unittest.TestCase):

    @patch("lighthouse.log.CLIHandler")
    @patch("lighthouse.log.logging")
    def test_setup_adds_handler_to_root_logger(self, mock_logging, CLIHandler):
        log.setup("foobar")

        mock_logging.getLogger.assert_called_once_with()
        mock_logging.getLogger.return_value.addHandler.assert_called_once_with(
            CLIHandler()
        )
