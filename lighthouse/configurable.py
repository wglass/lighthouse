class Configurable(object):
    """
    Base class for targets configured by the config file watching system.

    Each subclass is expected to be able to validate and apply configuration
    dictionaries that come from config file content.
    """

    name = None

    # This attribute denotes that the config watching system should check
    # a subdirectory for this configurable's files.
    config_subdirectory = None

    @classmethod
    def validate_config(cls, config):
        """
        Validates a given config, returns the validated config dictionary
        if valid, raises a ValueError for any invalid values.

        Subclasses are expected to define this method.
        """
        raise NotImplementedError

    def apply_config(self, config):
        """
        Applies a given config to the subclass.

        Setting instance attributes, for example.  Subclasses are expected
        to define this method.

        NOTE: It is *incredibly important* that this method be idempotent with
        regards to the instance.
        """
        raise NotImplementedError

    @classmethod
    def from_config(cls, name, config):
        """
        Returns a Configurable instance with the given name and config.

        By default this is a simple matter of calling the constructor, but
        subclasses that are also `Pluggable` instances override this in order
        to check that the plugin is installed correctly first.
        """

        cls.validate_config(config)

        instance = cls()
        if not instance.name:
            instance.name = config.get("name", name)
        instance.apply_config(config)

        return instance
