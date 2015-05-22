try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch, Mock

from lighthouse.service import Service


class ServiceTests(unittest.TestCase):

    def test_port_is_required(self):
        self.assertRaises(
            ValueError,
            Service.validate_config,
            {
                "host": "localhost",
                "checks": {"interval": 2},
                "interval": 2,
                "discovery": "zookeeper",
                "foo": "bar"
            }
        )

    def test_checks_is_required(self):
        self.assertRaises(
            ValueError,
            Service.validate_config,
            {
                "host": "localhost",
                "port": 3333,
                "interval": 2,
                "discovery": "zookeeper",
                "foo": "bar"
            }
        )

    def test_checks_interval_is_required(self):
        self.assertRaises(
            ValueError,
            Service.validate_config,
            {
                "host": "localhost",
                "port": 3333,
                "checks": {},
                "discovery": "zookeeper",
                "foo": "bar"
            }
        )

    def test_discovery_is_required(self):
        self.assertRaises(
            ValueError,
            Service.validate_config,
            {
                "host": "localhost",
                "port": 3333,
                "checks": {"interval": 2},
                "interval": 2,
                "foo": "bar"
            }
        )

    def test_is_up_defaults_to_none(self):
        service = Service()

        self.assertEqual(service.is_up, None)

    @patch("lighthouse.service.Check")
    def test_apply_config_handles_handles_valueerror(self, Check):
        Check.from_config.side_effect = ValueError

        service = Service()
        service.apply_config({
            "host": "localhost",
            "port": 3333,
            "discovery": "zookeeper",
            "checks": {
                "interval": 2,
                "http": {"host": "localhost", "port": 8888}
            }
        })

        self.assertEqual(service.checks, {})

        Check.from_config.assert_called_once_with(
            service, "http", {"host": "localhost", "port": 8888}
        )

    @patch("lighthouse.service.Check")
    def test_apply_config_with_checks(self, Check):
        check = Mock(config={"foo": "bar"})
        Check.from_config.return_value = check

        service = Service()
        service.apply_config({
            "host": "localhost",
            "port": 3333,
            "discovery": "zookeeper",
            "checks": {
                "interval": 2,
                "http": {"host": "localhost", "port": 8888}
            }
        })

        self.assertEqual(service.checks, {"http": check})

    @patch("lighthouse.service.Check")
    def test_apply_config_with_existing_check(self, Check):
        check = Mock(config={"foo": "bar"})
        Check.from_config.return_value = check

        service = Service()

        service.checks = {
            "http": check
        }

        service.apply_config({
            "host": "localhost",
            "port": 3333,
            "discovery": "zookeeper",
            "checks": {
                "interval": 2,
                "http": {"host": "localhost", "port": 8888}
            }
        })

        self.assertEqual(service.checks, {"http": check})

        check.apply_config.assert_called_once_with(
            {"host": "localhost", "port": 8888}
        )
