try:
    import unittest2 as unittest
except ImportError:
    import unittest

import os

from mock import patch, Mock, call

from lighthouse.configs.monitor import ConfigFileMonitor


class TestTarget(object):
    name = "target"
    config_subdirectory = None


class TestTargetWithSubdir(object):
    name = "target"
    config_subdirectory = "bazz"


@patch("lighthouse.configs.monitor.os")
class ConfigMonitorTests(unittest.TestCase):

    def test_file_path(self, mock_os):
        monitor = ConfigFileMonitor(TestTarget, "/etc/foobar")

        self.assertEqual(
            monitor.file_path,
            mock_os.path.join.return_value
        )

        mock_os.path.join.assert_called_once_with("/etc/foobar")

    def test_adds_subdirectory_to_file_path(self, mock_os):
        monitor = ConfigFileMonitor(TestTargetWithSubdir, "/etc/foobar")

        self.assertEqual(
            monitor.file_path,
            mock_os.path.join.return_value
        )

        mock_os.path.join.assert_called_once_with(
            "/etc/foobar", "bazz"
        )

    @patch("lighthouse.configs.monitor.observers")
    @patch("lighthouse.configs.monitor.ConfigFileChangeHandler")
    def test_passing_callbacks_to_handler(self, Handler, observers, mock_os):
        observer = observers.Observer.return_value

        monitor = ConfigFileMonitor(TestTarget, "/etc/foobar")

        on_add = Mock()
        on_update = Mock()
        on_delete = Mock()

        result = monitor.start(on_add, on_update, on_delete)

        Handler.assert_called_once_with(
            TestTarget, on_add, on_update, on_delete
        )

        self.assertEqual(result, observer)

        observer.schedule.assert_called_once_with(
            Handler.return_value, monitor.file_path
        )
        observer.start.assert_called_once_with()

    @patch("lighthouse.configs.monitor.observers.Observer.start")
    @patch("lighthouse.configs.monitor.events")
    @patch("lighthouse.configs.monitor.ConfigFileChangeHandler")
    def test_monitored_files_no_subdir(self, Handler, events, start, mock_os):

        def join_with_slashes(*paths):
            return "/".join(paths)

        mock_os.path.join.side_effect = join_with_slashes

        mock_os.listdir.return_value = [
            "a_subdir",  # a subdirectory, skipped
            "somefile.conf",  # does not match target name, skipped
            "target.yaml",
            "target.ini",  # not a yaml file, skipped
        ]
        are_dirs = [True, False, False, False]
        mock_os.path.isdir.side_effect = lambda f: are_dirs.pop(0)

        monitor = ConfigFileMonitor(TestTarget, "/etc/foobar")
        monitor.file_path = os.path.dirname(__file__)

        def on_add(*args):
            pass

        def on_update(*args):
            pass

        def on_delete(*args):
            pass

        monitor.start(on_add, on_update, on_delete)

        Handler.return_value.on_created.assert_called_with(
            events.FileCreatedEvent.return_value
        )
        events.FileCreatedEvent.assert_called_with(
            mock_os.path.join(os.path.dirname(__file__), "target.yaml")
        )

    @patch("lighthouse.configs.monitor.observers.Observer.start")
    @patch("lighthouse.configs.monitor.events")
    @patch("lighthouse.configs.monitor.ConfigFileChangeHandler")
    def test_monitored_files_subdir(self, Handler, events, start, mock_os):

        def join_with_slashes(*paths):
            return "/".join(paths)

        mock_os.path.join.side_effect = join_with_slashes

        mock_os.listdir.return_value = [
            "a_subdir",  # a subdirectory, skipped
            "afile.conf",
            "target.yaml",
            "target.ini",
        ]
        are_dirs = [True, False, False, False]
        mock_os.path.isdir.side_effect = lambda f: are_dirs.pop(0)

        monitor = ConfigFileMonitor(TestTargetWithSubdir, "/etc/foobar")
        monitor.file_path = os.path.dirname(__file__)

        def on_add(*args):
            pass

        def on_update(*args):
            pass

        def on_delete(*args):
            pass

        monitor.start(on_add, on_update, on_delete)

        Handler.return_value.on_created.assert_called_with(
            events.FileCreatedEvent.return_value
        )
        events.FileCreatedEvent.assert_has_calls([
            call(mock_os.path.join(os.path.dirname(__file__), "afile.conf")),
            call(mock_os.path.join(os.path.dirname(__file__), "target.yaml")),
            call(mock_os.path.join(os.path.dirname(__file__), "target.ini")),
        ])
