from mock import patch, call, Mock

from tests import cases

from lighthouse.configs.watcher import ConfigWatcher


class Thing(object):
    pass


class Widget(object):
    pass


class TestWatcher(ConfigWatcher):

    watched_configurables = (Thing, Widget)

    def __init__(self, *args, **kwargs):
        super(TestWatcher, self).__init__(*args, **kwargs)

        self.wind_down_called = False

    def wind_down(self):
        self.wind_down_called = True


class ConfigWatcherTests(cases.WatcherTestCase):

    def test_shutdown_event_unset_by_default(self):
        watcher = ConfigWatcher("/etc/configs/")

        self.assertEqual(watcher.shutdown.is_set(), False)

    def test_wind_down_must_be_defined(self):
        watcher = ConfigWatcher("/etc/configs/")

        self.assertRaises(
            NotImplementedError,
            watcher.wind_down
        )

    def test_adding_a_configurable(self):
        watcher = TestWatcher("/etc/configs/")

        thing = Thing()
        thing.name = "thing"

        watcher.add_configurable(Thing, "thing_1", thing)

        self.assertEqual(
            watcher.configurables[Thing],
            {
                "thing_1": thing
            }
        )

    def test_adding_a_configurable__with_hook(self):
        watcher = TestWatcher("/etc/configs/")
        watcher.on_thing_add = Mock()

        thing = Thing()
        thing.name = "thing"

        watcher.add_configurable(Thing, "thing", thing)

        watcher.on_thing_add.assert_called_once_with(thing)

    def test_adding_existing_configurable(self):
        watcher = TestWatcher("/etc/configs/")
        watcher.on_thing_add = Mock()
        watcher.update_configurable = Mock()

        thing = Thing()
        thing.name = "thing"

        watcher.configurables[Thing] = {
            "thing_1": Mock()
        }

        watcher.add_configurable(Thing, "thing_1", thing)

        assert watcher.on_thing_add.called is True

    def test_updating_configurable(self):
        watcher = TestWatcher("/etc/configs/")

        thing = Thing()
        thing.apply_config = Mock()

        watcher.configurables[Thing] = {
            "thing_1": thing
        }

        watcher.update_configurable(
            Thing, "thing_1", {"new": "config"}
        )

        thing.apply_config.assert_called_once_with({"new": "config"})

    def test_updating_uknown_configurable(self):
        watcher = TestWatcher("/etc/configs/")
        watcher.add_configurable = Mock()

        Thing.from_config = Mock()

        thing = Thing()
        thing.name = "thing_1"
        thing.config = {"old": "config"}
        thing.apply_config = Mock()

        watcher.configurables[Thing] = {
            "other_thing": thing
        }

        watcher.update_configurable(
            Thing, "thing_1", {"new": "config"}
        )

        assert thing.apply_config.called is False

        watcher.add_configurable.assert_called_once_with(
            Thing, Thing.from_config.return_value
        )
        Thing.from_config.assert_called_once_with(
            "thing_1", {"new": "config"}
        )

    def test_updating_configurable_with_hook(self):
        watcher = TestWatcher("/etc/configs/")
        watcher.on_thing_update = Mock()

        thing = Thing()
        thing.name = "thing_1"
        thing.config = {"old": "config"}
        thing.apply_config = Mock()

        watcher.configurables[Thing] = {
            "thing_1": thing
        }

        watcher.update_configurable(
            Thing, "thing_1", {"new": "config"}
        )

        watcher.on_thing_update.assert_called_with(
            "thing_1", {"new": "config"}
        )

    def test_removing_configurable(self):
        watcher = TestWatcher("/etc/configs/")

        thing = Thing()
        thing.name = "thing_1"
        thing.config = {"old": "config"}
        thing.apply_config = Mock()

        watcher.configurables[Thing] = {
            "thing_1": thing
        }

        watcher.remove_configurable(Thing, "thing_1")

        self.assertEqual(watcher.configurables[Thing], {})

    def test_removing_configurable_with_hook(self):
        watcher = TestWatcher("/etc/configs/")
        watcher.on_thing_remove = Mock()

        thing = Thing()
        thing.name = "thing_1"
        thing.config = {"old": "config"}
        thing.apply_config = Mock()

        watcher.configurables[Thing] = {
            "thing_1": thing
        }

        watcher.remove_configurable(Thing, "thing_1")

        watcher.on_thing_remove.assert_called_once_with("thing_1")

    def test_removing_unknown_configurable(self):
        watcher = TestWatcher("/etc/configs/")
        watcher.on_thing_remove = Mock()

        thing = Thing()
        thing.name = "thing_1"
        thing.config = {"old": "config"}
        thing.apply_config = Mock()

        watcher.configurables[Thing] = {
            "other_thing": thing
        }

        watcher.remove_configurable(Thing, "thing_1")

        assert watcher.on_thing_remove.called is False

    @patch("lighthouse.configs.watcher.ConfigFileMonitor")
    def test_start_creates_observers(self, Monitor):
        watcher = TestWatcher("/etc/configs")

        watcher.shutdown.set()

        watcher.start()

        self.assertEqual(
            watcher.observers,
            [
                Monitor.return_value.start.return_value,
                Monitor.return_value.start.return_value
            ]
        )
        Monitor.return_value.start.assert_has_calls([
            call(
                watcher.add_configurable,
                watcher.update_configurable,
                watcher.remove_configurable
            ),
            call(
                watcher.add_configurable,
                watcher.update_configurable,
                watcher.remove_configurable
            ),
        ])

        Monitor.assert_any_call(Thing, "/etc/configs")
        Monitor.assert_any_call(Widget, "/etc/configs")

    def test_stop_stops_observers(self):
        watcher = TestWatcher("/etc/confs")

        observer1 = Mock()
        observer2 = Mock()

        watcher.observers = [observer1, observer2]

        watcher.stop()

        observer1.stop.assert_called_once_with()
        observer1.join.assert_called_once_with()
        observer2.stop.assert_called_once_with()
        observer2.join.assert_called_once_with()

    def test_stop_sets_shutdown_flag(self):
        watcher = TestWatcher("/etc/conf")

        watcher.stop()

        self.assertEqual(watcher.shutdown.is_set(), True)
