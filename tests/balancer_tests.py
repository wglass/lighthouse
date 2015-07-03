try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch, Mock

from lighthouse.balancer import Balancer


class Balancertests(unittest.TestCase):

    def test_entrypoint(self):
        self.assertEqual(Balancer.entry_point, "lighthouse.balancers")

    @patch.object(Balancer, "apply_config")
    @patch.object(Balancer, "validate_config")
    def test_sync_file_must_be_implemented(self, validate, apply):
        balancer = Balancer()

        self.assertRaises(
            NotImplementedError,
            balancer.sync_file,
            [Mock(), Mock()]
        )

    @patch.object(Balancer, "get_installed_classes")
    def test_from_config(self, get_installed_classes):
        MockBalancer = Mock()
        get_installed_classes.return_value = {"riak": MockBalancer}

        balancer = Balancer.from_config("riak", {"foo": "bar"})

        self.assertEqual(balancer, MockBalancer.return_value)
        balancer.apply_config.assert_called_once_with({"foo": "bar"})

    @patch.object(Balancer, "get_installed_classes")
    def test_from_config_with_unknown_name(self, get_installed_classes):
        get_installed_classes.return_value = {"riak": Balancer}

        self.assertRaises(
            ValueError,
            Balancer.from_config, "zookeeper", {}
        )
