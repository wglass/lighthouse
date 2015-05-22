import logging

from .configurable import Configurable
from .balancer import Balancer


logger = logging.getLogger(__name__)


class Cluster(Configurable):
    """
    The class representing a cluster of member nodes in a service.

    A simple class that merely keeps a list of nodes and defines which
    discovery method is used to track said nodes.
    """

    config_subdirectory = "clusters"

    def __init__(self):
        self.discovery = None
        self.meta_cluster = None
        self.nodes = []

    @classmethod
    def validate_config(cls, config):
        """
        Validates a config dictionary parsed from a cluster config file.

        Checks that a discovery method is defined and that at least one of
        the balancers in the config are installed and available.
        """
        if "discovery" not in config:
            raise ValueError("No discovery method defined.")

        installed_balancers = Balancer.get_installed_classes().keys()

        if not any([balancer in config for balancer in installed_balancers]):
            raise ValueError("No available balancer configs defined.")

    def apply_config(self, config):
        """
        Sets the `discovery` and `meta_cluster` attributes, as well as the
        configured + available balancer attributes from a given validated
        config.
        """
        self.discovery = config["discovery"]
        self.meta_cluster = config.get("meta_cluster")
        for balancer_name in Balancer.get_installed_classes().keys():
            if balancer_name in config:
                setattr(self, balancer_name, config[balancer_name])
