import logging
import pkg_resources

from .configurable import Configurable


logger = logging.getLogger(__name__)


class Pluggable(Configurable):
    """
    Base class for classes that can be defined via external plugins.

    Subclasses define their `entry_point` attribute and subsequent calls to
    `get_installed_classes` will look up any available classes associated
    with that endpoint.

    Entry points used by lighthouse can be found in `setup.py` in the root
    of the project.
    """

    # the "entry point" for a plugin (e.g. "lighthouse.checks")
    entry_point = None

    @classmethod
    def validate_dependencies(cls):
        """
        Validates a plugin's external dependencies.  Should return True if
        all dependencies are met and False if not.

        Subclasses are expected to define this method.
        """
        raise NotImplementedError

    @classmethod
    def get_installed_classes(cls):
        """
        Iterates over installed plugins associated with the `entry_point` and
        returns a dictionary of viable ones keyed off of their names.

        A viable installed plugin is one that is both loadable *and* a subclass
        of the Pluggable subclass in question.
        """
        installed_classes = {}
        for entry_point in pkg_resources.iter_entry_points(cls.entry_point):
            try:
                plugin = entry_point.load()
            except ImportError as e:
                logger.error(
                    "Could not load plugin %s: %s", entry_point.name, str(e)
                )
                continue

            if not issubclass(plugin, cls):
                logger.error(
                    "Could not load plugin %s:" +
                    " %s class is not subclass of %s",
                    entry_point.name, plugin.__class__.__name__, cls.__name__
                )
                continue

            if not plugin.validate_dependencies():
                logger.error(
                    "Could not load plugin %s:" +
                    " %s class dependencies not met",
                    entry_point.name, plugin.__name__
                )
                continue

            installed_classes[entry_point.name] = plugin

        return installed_classes

    @classmethod
    def from_config(cls, name, config):
        """
        Behaves like the base Configurable class's `from_config()` except this
        makes sure that the `Pluggable` subclass with the given name is
        actually a properly installed plugin first.
        """
        installed_classes = cls.get_installed_classes()

        if name not in installed_classes:
            raise ValueError("Unknown/unavailable %s" % cls.__name__.lower())

        pluggable_class = installed_classes[name]

        pluggable_class.validate_config(config)

        instance = pluggable_class()
        if not instance.name:
            instance.name = name
        instance.apply_config(config)

        return instance
