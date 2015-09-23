import logging
import logging.config

from lighthouse.configurable import Configurable


log = logging.getLogger(__name__)


class Logging(Configurable):
    """
    Simple `Configurable` subclass that allows for runtime configuration of
    python's logging infrastructure.

    Since python provides a handy `dictConfig` function and our system already
    provides the watched file contents as dicts the work here is tiny.
    """

    name = "logging"

    @classmethod
    def from_config(cls, name, config):
        """
        Override of the base `from_config()` method that returns `None` if
        the name of the config file isn't "logging".

        We do this in case this `Configurable` subclass winds up sharing the
        root of the config directory with other subclasses.
        """
        if name != cls.name:
            return

        return super(Logging, cls).from_config(name, config)

    @classmethod
    def validate_config(cls, config):
        """
        The validation of a logging config is a no-op at this time, the call
        to dictConfig() when the config is applied will do the validation
        for us.
        """
        pass

    def apply_config(self, config):
        """
        Simple application of the given config via a call to the `logging`
        module's `dictConfig()` method.
        """
        logging.config.dictConfig(config)
