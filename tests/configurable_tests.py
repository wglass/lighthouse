try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from lighthouse.configurable import Configurable


class ConfigurableTests(unittest.TestCase):

    def test_validate_config_must_be_overridden(self):
        self.assertRaises(
            NotImplementedError,
            Configurable.validate_config,
            {"foo": "bar"}
        )

    @patch.object(Configurable, "validate_config")
    def test_apply_config_must_be_overridden(self, validate):
        patcher = patch.object(Configurable, "apply_config")
        patcher.start()

        configurable = Configurable()

        patcher.stop()

        self.assertRaises(
            NotImplementedError,
            configurable.apply_config,
            {"foo": "bar"}
        )

    @patch.object(Configurable, "validate_config")
    @patch.object(Configurable, "apply_config")
    def test_from_config_validates_and_applies_config(self, validate, apply):
        configurable = Configurable.from_config("something", {"foo": "bar"})

        self.assertEqual(configurable.name, "something")

        validate.assert_called_once_with({"foo": "bar"})
        apply.assert_called_once_with({"foo": "bar"})
