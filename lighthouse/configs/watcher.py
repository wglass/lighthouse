import logging
import threading

from .monitor import ConfigFileMonitor


logger = logging.getLogger(__name__)


class ConfigWatcher(object):
    """
    Base class for watchers that monitor and maintain `Configurable` instances.

    Subclasses define which `Configurable` subclasses they watch via the
    `watched_configurables` attribute as well as implement the `run()` and
    `wind_down()` methods.

    Optionally, subclasses can also define "on_<configurable>_<action>" methods
    (e.g. "on_service_update") that will hook into the add/update/remove
    configurable callbacks.

    .. warning::
       Care must be taken that these hooks are idempotent with regards
       to the Watcher subclass instance.  Configuration changes are liable to
       happen at any time and in any order.
    """

    # the list or tuple of Configurable subclasses to watch
    watched_configurables = ()

    def __init__(self, config_dir):
        self.config_dir = config_dir

        self.observers = []
        self.configurables = {}
        for config_class in self.watched_configurables:
            self.configurables[config_class] = {}

        self.shutdown = threading.Event()

    def start(self):
        """
        Iterates over the `watched_configurabes` attribute and starts a
        config file monitor for each.  The resulting observer threads are
        kept in an `observers` list attribute.
        """
        for config_class in self.watched_configurables:
            monitor = ConfigFileMonitor(config_class, self.config_dir)
            self.observers.append(
                monitor.start(
                    self.add_configurable,
                    self.update_configurable,
                    self.remove_configurable
                )
            )

        self.run()

    def run(self):
        """
        This method is called once the config file monitors are started.

        Subclasses are expected to implement this.
        """
        raise NotImplementedError

    def wind_down(self):
        """
        This method is called in the `stop()` method once the config file
        observers are stopped but before any threads are joined.

        Subclasses are expected to implement this.
        """
        raise NotImplementedError

    def add_configurable(self, configurable_class, name, configurable):
        """
        Callback fired when a configurable instance is added.

        Adds the configurable to the proper "registry" and calls a method
        named "on_<configurable classname>_add" if it is defined.

        If the added configurable is already present, `update_configurable()`
        is called instead.
        """
        configurable_class_name = configurable_class.__name__.lower()

        logger.info(
            "Adding %s: '%s'", configurable_class_name, name
        )

        registry = self.registry_for(configurable_class)

        if name in registry:
            logger.warn(
                "Adding already-existing %s: '%s'",
                configurable_class_name, name
            )

        registry[name] = configurable

        hook = self.hook_for(configurable_class, action="add")
        if hook:
            hook(configurable)

    def update_configurable(self, configurable_class, name, config):
        """
        Callback fired when a configurable instance is updated.

        Looks up the existing configurable in the proper "registry" and
        `apply_config()` is called on it.

        If a method named "on_<configurable classname>_update" is defined it
        is called and passed the configurable's name, the old config and the
        new config.

        If the updated configurable is not present, `add_configurable()` is
        called instead.
        """
        configurable_class_name = configurable_class.__name__.lower()

        logger.info(
            "updating %s: '%s'", configurable_class_name, name
        )

        registry = self.registry_for(configurable_class)

        if name not in registry:
            logger.warn(
                "Tried to update unknown %s: '%s'",
                configurable_class_name, name
            )
            self.add_configurable(
                configurable_class,
                configurable_class.from_config(name, config)
            )
            return

        registry[name].apply_config(config)

        hook = self.hook_for(configurable_class, "update")
        if hook:
            hook(name, config)

    def remove_configurable(self, configurable_class, name):
        """
        Callback fired when a configurable instance is removed.

        Looks up the existing configurable in the proper "registry" and
        removes it.

        If a method named "on_<configurable classname>_remove" is defined it
        is called and passed the configurable's name.
        If the removed configurable is not present, a warning is given and no
        further action is taken.
        """
        configurable_class_name = configurable_class.__name__.lower()

        logger.info("Removing %s: '%s'", configurable_class_name, name)

        registry = self.registry_for(configurable_class)

        if name not in registry:
            logger.warn(
                "Tried to remove unknown active %s: '%s'",
                configurable_class_name, name
            )
            return

        hook = self.hook_for(configurable_class, action="remove")
        if hook:
            hook(name)

        registry.pop(name)

    def registry_for(self, configurable_class):
        """
        Helper method for retrieving the "registry" dictionary of a given
        Configurable subclass.

        For example, the registry of Cluster instances for a config watcher
        would be `self.configurables[Cluster]`.
        """
        return self.configurables[configurable_class]

    def hook_for(self, configurable_class, action):
        """
        Helper method for determining if an on_<configurable class>_<action>
        method is present, to be used as a hook in the add/update/remove
        configurable methods.
        """
        configurable_class_name = configurable_class.__name__.lower()

        return getattr(
            self,
            "on_" + configurable_class_name + "_" + action,
            None
        )

    def stop(self):
        """
        Method for shutting down the watcher.

        All config file observers are stopped and their threads joined, along
        with the worker thread pool.
        """
        for monitor in self.observers:
            monitor.stop()

        self.shutdown.set()

        self.wind_down()

        for monitor in self.observers:
            monitor.join()
