import threading
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch, Mock

from lighthouse.discovery import Discovery


class DiscoveryTests(unittest.TestCase):

    def test_validate_dependencies_requried(self):
        self.assertRaises(
            NotImplementedError,
            Discovery.validate_dependencies
        )

    @patch.object(Discovery, "validate_dependencies", True)
    @patch.object(Discovery, "get_installed_classes")
    def test_from_config_with_unknown_name(self, get_installed_classes):
        get_installed_classes.return_value = {"riak": Discovery}

        self.assertRaises(
            ValueError,
            Discovery.from_config, "zookeeper", {}
        )

    @patch.object(Discovery, "validate_dependencies", True)
    @patch.object(Discovery, "get_installed_classes")
    def test_from_config(self, get_installed_classes):
        MockDiscovery = Mock()
        get_installed_classes.return_value = {"riak": MockDiscovery}

        discovery = Discovery.from_config("riak", {"foo": "bar"})

        self.assertEqual(discovery, MockDiscovery.return_value)
        discovery.apply_config.assert_called_once_with({"foo": "bar"})

    def test_connect_required(self):
        discovery = Discovery()

        self.assertRaises(NotImplementedError, discovery.connect)

    def test_start_watching_required(self):
        discovery = Discovery()

        self.assertRaises(
            NotImplementedError,
            discovery.start_watching, Mock(), threading.Event()
        )

    def test_stop_watching_required(self):
        discovery = Discovery()

        self.assertRaises(
            NotImplementedError,
            discovery.stop_watching, Mock()
        )

    def test_report_up_required(self):
        discovery = Discovery()

        self.assertRaises(
            NotImplementedError,
            discovery.report_up, Mock()
        )

    def test_report_down_required(self):
        discovery = Discovery()

        self.assertRaises(
            NotImplementedError,
            discovery.report_down, Mock()
        )

    def test_disconnect_required(self):
        discovery = Discovery()

        self.assertRaises(NotImplementedError, discovery.disconnect)

    @patch.object(Discovery, "disconnect")
    def test_stop_sets_shutdown_event(self, disconnect):
        discovery = Discovery()

        self.assertEqual(discovery.shutdown.is_set(), False)

        discovery.stop()

        self.assertEqual(discovery.shutdown.is_set(), True)

    @patch.object(Discovery, "disconnect")
    def test_stop_calls_disconnect(self, disconnect):
        discovery = Discovery()

        discovery.stop()

        disconnect.assert_called_once_with()
