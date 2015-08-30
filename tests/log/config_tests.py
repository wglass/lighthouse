try:
    import unittest2 as unittest
except ImportError:
    import unittest
import sys

from mock import patch, mock_open

from lighthouse.log import config


if sys.version_info[0] == 3:
    builtin_module = "builtins"
else:
    builtin_module = "__builtin__"


@patch("lighthouse.log.config.logging")
class LogConfigTests(unittest.TestCase):

    @patch("lighthouse.log.config.yaml")
    def test_load_yaml(self, mock_yaml, mock_logging):
        fake_file = mock_open()

        with patch(builtin_module + ".open", fake_file):
            config.load_yaml("/etc/logging.yaml")

        mock_yaml.load.assert_called_once_with(fake_file.return_value)
        mock_logging.config.dictConfig.assert_called_once_with(
            mock_yaml.load.return_value
        )

    def test_load_json(self, mock_logging):

        content = """
{
    "version": 1,
    "disable_existing_loggers": false,
    "loggers": {
        "lighthouse": {
            "handlers": ["syslog"],
            "level": "DEBUG",
            "propagate": true
        }
    }
}
        """

        with patch(builtin_module + ".open", mock_open(read_data=content)):
            config.load_json("/etc/logging.json")

        mock_logging.config.dictConfig.assert_called_once_with({
            "version": 1,
            "disable_existing_loggers": False,
            "loggers": {
                "lighthouse": {
                    "handlers": ["syslog"],
                    "level": "DEBUG",
                    "propagate": True
                }
            }
        })

    def test_load_init(self, mock_logging):
        config.load_ini("/etc/log.ini")

        mock_logging.config.fileConfig.assert_called_once_with("/etc/log.ini")
