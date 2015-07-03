import logging
import threading

from .pluggable import Pluggable


logger = logging.getLogger(__name__)


class Discovery(Pluggable):
    """
    Base class for discovery method plugins.

    Unlike the `Balancer` base class for load balancer plugins, this discovery
    method plugin has several methods that subclasses are expected to define.

    Subclasses are used for both the writer process *and* the reporter process
    so each subclass needs to be able to report on individual nodes as well
    as monitor and collect the status of all defined clusters.

    It is important that the various instances of lighthouse running on various
    machines agree with each other on the status of clusters so a distributed
    system with strong CP characteristics is recommended.
    """

    config_subdirectory = "discovery"
    entry_point = "lighthouse.discovery"

    def __init__(self):
        self.shutdown = threading.Event()

    def connect(self):
        """
        Subclasses should define this method to handle any sort of connection
        establishment needed.
        """
        raise NotImplementedError

    def disconnect(self):
        """
        This method is used to facilitate any shutting down operations needed
        by the subclass (e.g. closing connections and such).
        """
        raise NotImplementedError

    def start_watching(self, cluster, should_update):
        """
        Method called whenever a new cluster is defined and must be monitored
        for changes to nodes.

        Once a cluster is being successfully watched that cluster *must* be
        added to the `self.watched_clusters` set!

        Whenever a change is detected, the given `should_update` threading
        event should be set.
        """
        raise NotImplementedError

    def stop_watching(self, cluster):
        """
        This method should halt any of the monitoring started that would be
        started by a call to `start_watching()` with the same cluster.

        Once the cluster is no longer being watched that cluster *must* be
        removed from the `self.watched_clusters` set!
        """
        raise NotImplementedError

    def report_up(self, service, port):
        """
        This method is used to denote that the given service present on the
        current machine should be considered up and available.
        """
        raise NotImplementedError

    def report_down(self, service, port):
        """
        This method is used to denote that the given service present on the
        current machine should be considered down and unavailable.
        """
        raise NotImplementedError

    def stop(self):
        """
        Simple method that sets the `shutdown` event and calls the subclass's
        `wind_down()` method.
        """
        self.shutdown.set()
        self.disconnect()
