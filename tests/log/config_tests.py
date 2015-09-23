try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from lighthouse.log import config


class LogConfigTests(unittest.TestCase):

    def test_validate_config_is_noop(self):
        self.assertEqual(
            config.Logging.validate_config({}),
            None
        )

    @patch("lighthouse.log.config.logging")
    def test_apply_config_calls_dictconfig(self, mock_logging):
        log = config.Logging()

        log.apply_config({"foo": "bar"})

        mock_logging.config.dictConfig.assert_called_once_with({"foo": "bar"})

    @patch("lighthouse.log.config.logging")
    def test_from_config_returns_none_on_name_mismatch(self, mock_logging):
        self.assertEqual(
            config.Logging.from_config("foobar", {"foo": "bar"}),
            None
        )

    @patch("lighthouse.log.config.logging")
    def test_from_config_with_matching_name(self, mock_logging):
        log = config.Logging.from_config("logging", {"foo": "bar"})

        self.assertNotEqual(log, None)

        self.assertEqual(log.name, "logging")
