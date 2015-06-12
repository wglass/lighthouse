try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch, Mock

from lighthouse.coordinator import Coordinator


class Coordinatortests(unittest.TestCase):

    def test_entrypoint(self):
        self.assertEqual(Coordinator.entry_point, "lighthouse.coordinators")

    @patch.object(Coordinator, "apply_config")
    @patch.object(Coordinator, "validate_config")
    def test_sync_file_must_be_implemented(self, validate, apply):
        coordinator = Coordinator()

        self.assertRaises(
            NotImplementedError,
            coordinator.sync_file,
            [Mock(), Mock()]
        )

    @patch.object(Coordinator, "get_installed_classes")
    def test_from_config(self, get_installed_classes):
        MockCoordinator = Mock()
        get_installed_classes.return_value = {"riak": MockCoordinator}

        coordinator = Coordinator.from_config("riak", {"foo": "bar"})

        self.assertEqual(coordinator, MockCoordinator.return_value)
        coordinator.apply_config.assert_called_once_with({"foo": "bar"})

    @patch.object(Coordinator, "get_installed_classes")
    def test_from_config_with_unknown_name(self, get_installed_classes):
        get_installed_classes.return_value = {"riak": Coordinator}

        self.assertRaises(
            ValueError,
            Coordinator.from_config, "zookeeper", {}
        )
