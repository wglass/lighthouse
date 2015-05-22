try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch, Mock

from lighthouse.pluggable import Pluggable


class FakePlugin(Pluggable):
    entry_point = "fake.entrypoint"

    @classmethod
    def validate_dependencies(cls):
        return True


class OtherPlugin(Pluggable):
    entry_point = "other.entrypoint"

    name = "other"

    @classmethod
    def validate_dependencies(cls):
        return True

    @classmethod
    def validate_config(cls, config):
        return

    def apply_config(self, config):
        return


class IncompletePlugin(FakePlugin):
    entry_point = "fake.entrypoint"

    @classmethod
    def validate_dependencies(cls):
        return False


@patch("lighthouse.pluggable.pkg_resources")
class PluggableTests(unittest.TestCase):

    def test_get_installed_classes(self, pkg_resources):
        bad_plugin = Mock()
        bad_plugin.name = "bad"
        bad_plugin.load.side_effect = ImportError

        fake_plugin = Mock()
        fake_plugin.name = "fakeplugin"
        fake_plugin.load.return_value = FakePlugin

        incomplete_plugin = Mock()
        incomplete_plugin.name = "incomplete"
        incomplete_plugin.load.return_value = IncompletePlugin

        other_plugin = Mock()
        other_plugin.name = "other"
        other_plugin.load.return_value = OtherPlugin

        pkg_resources.iter_entry_points.return_value = [
            bad_plugin,
            fake_plugin,
            incomplete_plugin,
            other_plugin
        ]

        self.assertEqual(
            FakePlugin.get_installed_classes(),
            {"fakeplugin": FakePlugin}
        )

    @patch.object(FakePlugin, "validate_config")
    @patch.object(FakePlugin, "apply_config")
    def test_from_config(self, validate_config, apply_config, pkg_resources):
        fake_plugin = Mock()
        fake_plugin.name = "fakeplugin"
        fake_plugin.load.return_value = FakePlugin

        pkg_resources.iter_entry_points.return_value = [fake_plugin]

        result = Pluggable.from_config("fakeplugin", {"foo": "bar"})

        self.assertEqual(result.name, "fakeplugin")
        validate_config.assert_called_once_with({"foo": "bar"})
        result.apply_config.assert_called_once_with({"foo": "bar"})

    def test_from_config__unknown_plugin(self, pkg_resources):
        pkg_resources.iter_entry_points.return_value = []

        self.assertRaises(
            ValueError,
            FakePlugin.from_config, "thing", {}
        )

    def test_from_config__class_level_name(self, pkg_resources):
        other_plugin = Mock()
        other_plugin.name = "otherplugin"
        other_plugin.load.return_value = OtherPlugin

        pkg_resources.iter_entry_points.return_value = [other_plugin]

        result = Pluggable.from_config("otherplugin", {"foo": "bar"})

        self.assertEqual(result.name, "other")
