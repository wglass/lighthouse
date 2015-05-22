import logging
import threading

from .configs.watcher import ConfigWatcher
from .balancer import Balancer
from .cluster import Cluster
from .discovery import Discovery
from .events import wait_on_any, wait_on_event


logger = logging.getLogger(__name__)


class Writer(ConfigWatcher):
    """
    The load balancer configuration writing class.

    This ConfigWatcher subclass manages Discovery and Cluster and Balancer
    configurable instances.

    The Discovery and Cluster instances are kept in sync to make sure the
    proper discovery methods are watching the proper clusters.  Whenever a
    change takes place the Balancer instances are notified and syncs their
    config file contents with the updated clusters.
    """

    watched_configurables = (Balancer, Discovery, Cluster)

    def __init__(self, *args, **kwargs):
        super(Writer, self).__init__(*args, **kwargs)

        self.nodes_updated = threading.Event()

    def run(self):
        """
        Runs the main thread of the writer ConfigWatcher.

        This merely launches a separate thread for the config-file-updating
        loop and waits on the `shutdown` event.
        """
        logger.info("Running writer.")

        update_thread = threading.Thread(
            name="updates", target=self.wait_for_updates
        )
        update_thread.daemon = True
        update_thread.start()

        wait_on_event(self.shutdown)

    def wait_for_updates(self):
        """
        Writer update loop.

        The loop waits on either the `shutdown` or `nodes_updated` events
        to fire.  if the `shutdown` event is fired the loop is broken and we
        stop updating.If the `nodes_updated` event is set then all of the
        configured load balancers sync their config files.
        """
        while True:
            wait_on_any(self.shutdown, self.nodes_updated)

            if self.shutdown.is_set():
                break

            logger.debug("Update flag set.")
            for balancer in self.configurables[Balancer].values():
                balancer.sync_file(self.configurables[Cluster].values())
            self.nodes_updated.clear()

    def on_balancer_add(self, balancer):
        """
        Once a balancer is added we set the `nodes_updated` event so that we
        sync the config file right away.
        """
        balancer.sync_file(self.configurables[Cluster].values())
        self.nodes_updated.set()

    def on_balancer_update(self, name, new_config):
        """
        Sets the `nodes_updated` event so that we sync balancer config files
        whenever a balancer is updated.
        """
        self.nodes_updated.set()

    def on_balancer_remove(self, name):
        """
        The removal of a load balancer config is unusual but still supported.

        If the balancer being removed is the only configured one we fire
        a critical log message saying so.  A writer setup with no balancers
        is less than useless.
        """
        if len(self.configurables[Balancer]) == 1:
            logger.critical(
                "'%s' config file removed! no more balancers left!", name
            )

    def on_discovery_add(self, discovery):
        """
        When a discovery is added we call `connect()` on it and have it start
        watching for changes to any existing clusters that use the new
        discovery method.
        """
        discovery.connect()
        discovery.nodes_updated = self.nodes_updated

        for cluster in self.configurables[Cluster].values():
            if cluster.discovery != discovery.name:
                continue

            discovery.start_watching(cluster)

    def on_discovery_remove(self, name):
        """
        When a Discovery is removed we must make sure to call its `stop()`
        method to close any connections or do any clean up.
        """
        self.configurables[Discovery][name].stop()

    def on_cluster_add(self, cluster):
        """
        Once a cluster is added we tell its associated discovery method to
        start watching for changes to the cluster's child nodes (if the
        discovery method is configured and available).
        """
        if cluster.discovery not in self.configurables[Discovery]:
            return

        self.configurables[Discovery][cluster.discovery].start_watching(
            cluster
        )

    def on_cluster_update(self, name, new_config):
        """
        Callback hook for when a cluster is updated.

        Or main concern when a cluster is updated is whether or not the
        associated discovery method changed.  If it did, we make sure that
        the old discovery method stops watching for the cluster's changes (if
        the old method is around) and that the new method *starts* watching
        for the cluster's changes (if the new method is actually around).

        Regardless of how the discovery method shuffling plays out the
        `nodes_updated` flag is set so that we properly sync any balancer
        configurations.
        """
        cluster = self.configurables[Cluster][name]

        old_discovery = cluster.discovery
        new_discovery = new_config["discovery"]
        if old_discovery == new_discovery:
            self.nodes_updated.set()
            return

        logger.info(
            "Switching '%s' cluster discovery from '%s' to '%s'",
            name, old_discovery, new_discovery
        )

        if old_discovery in self.configurables[Discovery]:
            self.configurables[Discovery][old_discovery].stop_watching(
                cluster
            )
        if new_discovery not in self.configurables[Discovery]:
            logger.warn(
                "New discovery '%s' for cluster '%s' is unknown/unavailable.",
                new_discovery, name
            )
            self.nodes_updated.set()
            return

        self.configurables[Discovery][new_discovery].start_watching(cluster)

        self.nodes_updated.set()

    def on_cluster_remove(self, name):
        """
        Stops the cluster's associated discovery method from watching for
        changes to the cluster's nodes.
        """
        discovery_name = self.configurables[Cluster][name].discovery
        if discovery_name in self.configurables[Discovery]:
            self.configurables[Discovery][discovery_name].stop_watching(
                self.configurables[Cluster][name]
            )

    def wind_down(self):
        """
        Winding down a writer ConfigWatcher is merely a matter of stopping
        the present discovery methods.
        """
        for discovery in self.configurables[Discovery].values():
            discovery.stop()
