import logging
import threading

from concurrent import futures

from .monitor import ConfigFileMonitor
from lighthouse.events import wait_on_event


MAX_WORKERS = 8


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

        self.work_pool = futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.thread_pool = {}

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

        wait_on_event(self.shutdown)

    def wind_down(self):
        """
        This method is called in the `stop()` method once the config file
        observers are stopped but before any threads are joined.

        Subclasses are expected to implement this.
        """
        raise NotImplementedError

    def launch_thread(self, name, fn, *args, **kwargs):
        """
        Adds a named thread to the "thread pool" dictionary of Thread objects.

        A daemon thread that executes the passed-in function `fn` with the
        given args and keyword args is started and tracked in the `thread_pool`
        attribute with the given `name` as the key.
        """
        logger.debug(
            "Launching thread '%s': %s(%s, %s)", name,
            fn, args, kwargs
        )
        self.thread_pool[name] = threading.Thread(
            target=fn, args=args, kwargs=kwargs
        )
        self.thread_pool[name].daemon = True
        self.thread_pool[name].start()

    def kill_thread(self, name):
        """
        Joins the thread in the `thread_pool` dict with the given `name` key.
        """
        if name not in self.thread_pool:
            return

        self.thread_pool[name].join()
        del self.thread_pool[name]

    def add_configurable(self, configurable_class, name, configurable):
        """
        Callback fired when a configurable instance is added.

        Adds the configurable to the proper "registry" and calls a method
        named "on_<configurable classname>_add" in the work pool if the hook
        is defined.

        If the added configurable is already present, `update_configurable()`
        is called instead.
        """
        configurable_class_name = configurable_class.__name__.lower()

        logger.info("Adding %s: '%s'", configurable_class_name, name)

        registry = self.registry_for(configurable_class)

        if name in registry:
            logger.warn(
                "Adding already-existing %s: '%s'",
                configurable_class_name, name
            )

        registry[name] = configurable

        hook = self.hook_for(configurable_class, action="add")
        if not hook:
            return

        def done(f):
            try:
                f.result()
            except Exception:
                logger.exception("Error adding configurable '%s'", name)

        self.work_pool.submit(hook, configurable).add_done_callback(done)

    def update_configurable(self, configurable_class, name, config):
        """
        Callback fired when a configurable instance is updated.

        Looks up the existing configurable in the proper "registry" and
        `apply_config()` is called on it.

        If a method named "on_<configurable classname>_update" is defined it
        is called in the work pool and passed the configurable's name, the old
        config and the new config.

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
        if not hook:
            return

        def done(f):
            try:
                f.result()
            except Exception:
                logger.exception("Error updating configurable '%s'", name)

        self.work_pool.submit(hook, name, config).add_done_callback(done)

    def remove_configurable(self, configurable_class, name):
        """
        Callback fired when a configurable instance is removed.

        Looks up the existing configurable in the proper "registry" and
        removes it.

        If a method named "on_<configurable classname>_remove" is defined it
        is called via the work pooland passed the configurable's name.

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
        if not hook:
            registry.pop(name)
            return

        def done(f):
            try:
                f.result()
                registry.pop(name)
            except Exception:
                logger.exception("Error removing configurable '%s'", name)

        self.work_pool.submit(hook, name).add_done_callback(done)

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
        self.shutdown.set()

        for monitor in self.observers:
            monitor.stop()

        self.wind_down()

        for monitor in self.observers:
            monitor.join()

        for thread in self.thread_pool.values():
            thread.join()

        self.work_pool.shutdown()
