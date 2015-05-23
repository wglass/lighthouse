try:
    import unittest2 as unittest
except ImportError:
    import unittest

import sys

from mock import patch, Mock, mock_open

from watchdog import events

from lighthouse.configs.handler import ConfigFileChangeHandler


test_content = """
port: 8888
extras:
    - "foo"
    - "bar"
"""


if sys.version_info[0] == 3:
    builtin_module = "builtins"
else:
    builtin_module = "__builtin__"


@patch(builtin_module + ".open", mock_open(read_data=test_content))
class ConfigChangeHandlerTests(unittest.TestCase):

    @patch("lighthouse.configs.handler.os")
    def test_on_created_skips_dir_srcpaths(self, mock_os):
        target_class = Mock()
        created_event = Mock(src_path="/foo/bar")

        on_add = Mock()
        on_update = Mock()
        on_delete = Mock()

        mock_os.path.isdir.return_value = True

        handler = ConfigFileChangeHandler(
            target_class, on_add, on_update, on_delete
        )

        handler.on_created(created_event)

        assert on_add.called is False
        assert on_update.called is False
        assert on_delete.called is False

        mock_os.path.isdir.assert_called_once_with("/foo/bar")

    @patch("lighthouse.configs.handler.yaml")
    def test_on_created_config_error(self, yaml):
        yaml.load.return_value = {"port": 8888, "extras": ["foo", "bar"]}
        created_event = Mock(src_path="/foo/bar/service.yaml")

        on_add = Mock()
        on_update = Mock()
        on_delete = Mock()

        target_class = Mock()
        target_class.from_config.side_effect = ValueError

        handler = ConfigFileChangeHandler(
            target_class, on_add, on_update, on_delete
        )

        handler = ConfigFileChangeHandler(target_class, on_add, Mock(), Mock())

        handler.on_created(created_event)

        assert on_add.called is False
        assert on_update.called is False
        assert on_delete.called is False

        target_class.from_config.assert_called_once_with(
            "service", {"port": 8888, "extras": ["foo", "bar"]}
        )

    @patch("lighthouse.configs.handler.logger")
    @patch("lighthouse.configs.handler.yaml")
    def test_on_created_generic_error(self, yaml, mock_logger):
        yaml.load.return_value = {"port": 8888, "extras": ["foo", "bar"]}
        created_event = Mock(src_path="/foo/bar/service.yaml")

        on_add = Mock()
        on_update = Mock()
        on_delete = Mock()

        target_class = Mock()
        target_class.from_config.side_effect = Exception("oh no!")

        handler = ConfigFileChangeHandler(
            target_class, on_add, on_update, on_delete
        )

        handler = ConfigFileChangeHandler(target_class, on_add, Mock(), Mock())

        handler.on_created(created_event)

        assert on_add.called is False
        assert on_update.called is False
        assert on_delete.called is False

        self.assertEqual(mock_logger.exception.call_count, 1)

    @patch("lighthouse.configs.handler.yaml")
    def test_on_created(self, yaml):
        yaml.load.return_value = {"port": 8888, "extras": ["foo", "bar"]}
        created_event = Mock(src_path="/foo/bar/service.yaml")

        target_class = Mock()
        on_add = Mock()
        on_update = Mock()
        on_delete = Mock()

        handler = ConfigFileChangeHandler(
            target_class, on_add, on_update, on_delete
        )

        handler.on_created(created_event)

        on_add.assert_called_once_with(
            target_class, "service", target_class.from_config.return_value
        )
        assert on_update.called is False
        assert on_delete.called is False

    @patch("lighthouse.configs.handler.os")
    def test_on_modified_skips_dir_srcpaths(self, mock_os):
        target_class = Mock()
        modified_event = Mock(src_path="/foo/bar")

        on_add = Mock()
        on_update = Mock()
        on_delete = Mock()

        mock_os.path.isdir.return_value = True

        handler = ConfigFileChangeHandler(
            target_class, on_add, on_update, on_delete
        )

        handler.on_modified(modified_event)

        assert on_add.called is False
        assert on_update.called is False
        assert on_delete.called is False

        mock_os.path.isdir.assert_called_once_with("/foo/bar")

    @patch("lighthouse.configs.handler.yaml")
    def test_on_modified_config_error(self, yaml):
        yaml.load.return_value = {"port": 8888, "extras": ["foo", "bar"]}
        modified_event = Mock(src_path="/foo/bar/service.yaml")

        on_add = Mock()
        on_update = Mock()
        on_delete = Mock()

        target_class = Mock()
        target_class.from_config.side_effect = ValueError

        handler = ConfigFileChangeHandler(
            target_class, on_add, on_update, on_delete
        )

        handler.on_modified(modified_event)

        assert on_add.called is False
        assert on_update.called is False
        assert on_delete.called is False

        target_class.from_config.assert_called_once_with(
            "service", {"port": 8888, "extras": ["foo", "bar"]}
        )

    @patch("lighthouse.configs.handler.yaml")
    def test_on_modified_generic_error(self, yaml):
        yaml.load.return_value = {"port": 8888, "extras": ["foo", "bar"]}
        modified_event = Mock(src_path="/foo/bar/service.yaml")

        on_add = Mock()
        on_update = Mock()
        on_delete = Mock()

        target_class = Mock()
        target_class.from_config.side_effect = Exception

        handler = ConfigFileChangeHandler(
            target_class, on_add, on_update, on_delete
        )

        handler.on_modified(modified_event)

        assert on_add.called is False
        assert on_update.called is False
        assert on_delete.called is False

    @patch("lighthouse.configs.handler.yaml")
    def test_on_modified(self, yaml):
        yaml.load.return_value = {"port": 8888, "extras": ["foo", "bar"]}
        modified_event = Mock(src_path="/foo/bar/service.yaml")

        target_class = Mock()
        on_add = Mock()
        on_update = Mock()
        on_delete = Mock()

        handler = ConfigFileChangeHandler(
            target_class, on_add, on_update, on_delete
        )

        handler.on_modified(modified_event)

        on_update.assert_called_once_with(
            target_class, "service", yaml.load.return_value
        )
        target_class.from_config.assert_called_once_with(
            "service", yaml.load.return_value
        )
        assert on_add.called is False
        assert on_delete.called is False

    def test_on_delete(self):
        deleted_event = Mock(src_path="/foo/bar/service.yaml")

        target_class = Mock()
        on_add = Mock()
        on_update = Mock()
        on_delete = Mock()

        handler = ConfigFileChangeHandler(
            target_class, on_add, on_update, on_delete
        )

        handler.on_deleted(deleted_event)

        assert on_add.called is False
        assert on_update.called is False
        on_delete.assert_called_once_with(target_class, "service")

    @patch.object(ConfigFileChangeHandler, "on_deleted")
    @patch.object(ConfigFileChangeHandler, "on_created")
    def test_on_moved(self, on_created, on_deleted):
        moved_event = Mock(
            src_path="/foo/bar/service.yaml",
            dest_path="/foo/bar/newservice.yaml"
        )

        target_class = Mock()
        on_add = Mock()
        on_update = Mock()
        on_delete = Mock()

        handler = ConfigFileChangeHandler(
            target_class, on_add, on_update, on_delete
        )

        handler.on_moved(moved_event)

        on_deleted.assert_called_once_with(
            events.FileDeletedEvent("/foo/bar/service.yaml")
        )
        on_created.assert_called_once_with(
            events.FileCreatedEvent("/foo/bar/newservice.yaml")
        )
