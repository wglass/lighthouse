import collections
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
        self.ports = set()

        self.configured_ports = None

        self.discovery = None

        self.checks = collections.defaultdict(dict)
        self.check_interval = None

        self.is_up = collections.defaultdict(lambda: None)

        self.metadata = {}

    @classmethod
    def validate_config(cls, config):
        """
        Runs a check on the given config to make sure that `port`/`ports` and
        `discovery` is defined.
        """
        if "discovery" not in config:
            raise ValueError("No discovery method defined.")

        if not any([item in config for item in ["port", "ports"]]):
            raise ValueError("No port(s) defined.")

        cls.validate_check_configs(config)

    @classmethod
    def validate_check_configs(cls, config):
        """
        Config validation specific to the health check options.

        Verifies that checks are defined along with an interval, and calls
        out to the `Check` class to make sure each individual check's config
        is valid.
        """
        if "checks" not in config:
            raise ValueError("No checks defined.")
        if "interval" not in config["checks"]:
            raise ValueError("No check interval defined.")

        for check_name, check_config in six.iteritems(config["checks"]):
            if check_name == "interval":
                continue

            Check.from_config(check_name, check_config)

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

        self.configured_ports = config.get("ports", [config.get("port")])

        self.discovery = config["discovery"]

        self.metadata = config.get("metadata", {})

        self.update_ports()

        self.check_interval = config["checks"]["interval"]

        self.update_checks(config["checks"])

    def reset_status(self):
        """
        Sets the up/down status of the service ports to the default state.

        Useful for when the configuration is updated and the checks involved
        in determining the status might have changed.
        """
        self.is_up = collections.defaultdict(lambda: None)

    def update_ports(self):
        """
        Sets the `ports` attribute to the set of valid port values set in
        the configuration.
        """
        ports = set()

        for port in self.configured_ports:
            try:
                ports.add(int(port))
            except ValueError:
                logger.error("Invalid port value: %s", port)
                continue

        self.ports = ports

    def update_checks(self, check_configs):
        """
        Maintains the values in the `checks` attribute's dictionary.  Each
        key in the dictionary is a port, and each value is a nested dictionary
        mapping each check's name to the Check instance.

        This method makes sure the attribute reflects all of the properly
        configured checks and ports.  Removing no-longer-configured ports
        is left to the `run_checks` method.
        """
        for check_name, check_config in six.iteritems(check_configs):
            if check_name == "interval":
                continue

            for port in self.ports:
                try:
                    check = Check.from_config(check_name, check_config)
                    check.host = self.host
                    check.port = port
                    self.checks[port][check_name] = check
                except ValueError as e:
                    logger.error(
                        "Error when configuring check '%s' for service %s: %s",
                        check_name, self.name, str(e)
                    )
                    continue

    def run_checks(self):
        """
        Iterates over the configured ports and runs the checks on each one.

        Returns a two-element tuple: the first is the set of ports that
        transitioned from down to up, the second is the set of ports that
        transitioned from up to down.

        Also handles the case where a check for a since-removed port is run,
        marking the port as down regardless of the check's result and removing
        the check(s) for the port.
        """
        came_up = set()
        went_down = set()

        for port in self.ports:
            checks = self.checks[port].values()

            if not checks:
                logger.warn("No checks defined for self: %s", self.name)

            for check in checks:
                check.run()

            checks_pass = all([check.passing for check in checks])

            if self.is_up[port] in (False, None) and checks_pass:
                came_up.add(port)
                self.is_up[port] = True
            elif self.is_up[port] in (True, None) and not checks_pass:
                went_down.add(port)
                self.is_up[port] = False

        for unused_port in set(self.checks.keys()) - self.ports:
            went_down.add(unused_port)
            del self.checks[unused_port]

        return came_up, went_down
