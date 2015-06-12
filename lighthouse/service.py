import logging

import six

from .configurable import Configurable
from .check import Check


logger = logging.getLogger(__name__)


class Service(Configurable):
    """
    Class representing a service provided by the current machine.

    This is a straightforward Configurable subclass, it defines what a valid
    configuration for a service is and applies them.
    """

    config_subdirectory = "services"

    def __init__(self):
        self.host = None
        self.port = None
        self.discoery = None

        self.checks = {}
        self.check_interval = None
        self.is_up = None

        self.metadata = {}

    @classmethod
    def validate_config(cls, config):
        """
        Runs a check on the given config to make sure that `host`, `port`,
        `checks`, `discovery` and an interval for the checks is defined.
        """
        if "port" not in config:
            raise ValueError("Port not defined.")
        if "checks" not in config:
            raise ValueError("No checks defined.")
        if "interval" not in config["checks"]:
            raise ValueError("No check interval defined.")
        if "discovery" not in config:
            raise ValueError("No discovery method defined.")

        for check_name, check_config in six.iteritems(config["checks"]):
            if check_name == "interval":
                continue

            Check.from_config(
                check_name, config["host"], config["port"], check_config
            )

    def apply_config(self, config):
        """
        Takes a given validated config dictionary and sets an instance
        attribute for each one.

        For check definitions, a Check instance is is created and a `checks`
        attribute set to a dictionary keyed off of the checks' names.  If
        the Check instance has some sort of error while being created an error
        is logged and the check skipped.
        """
        self.host = config.get("host", "127.0.0.1")
        self.port = config["port"]
        self.discovery = config["discovery"]

        self.metadata = config.get("metadata", {})

        self.check_interval = config["checks"]["interval"]

        for check_name, check_config in six.iteritems(config["checks"]):
            if check_name == "interval":
                continue

            try:
                if check_name in self.checks:
                    self.checks[check_name].validate_config(check_config)
                    self.checks[check_name].apply_config(check_config)
                else:
                    self.checks[check_name] = Check.from_config(
                        check_name, self.host, self.port, check_config
                    )
            except ValueError as e:
                logger.error(
                    "Error when configuring check '%s' for service '%s': %s",
                    check_name, self.name, str(e)
                )
                continue
