import logging

from .configs.watcher import ConfigWatcher
from .log.config import Logging
from .balancer import Balancer
from .cluster import Cluster
from .discovery import Discovery


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

    watched_configurables = (Logging, Balancer, Discovery, Cluster)

    def sync_balancer_files(self):
        """
        Syncs the config files for each present Balancer instance.

        Submits the work to sync each file as a work pool job.
        """

        def sync():
            for balancer in self.configurables[Balancer].values():
                balancer.sync_file(self.configurables[Cluster].values())

        self.work_pool.submit(sync)

    def on_balancer_add(self, balancer):
        """
        Whenever a balancer is added we sync all of the balancer config files.
        """
        self.sync_balancer_files()

    def on_balancer_update(self, name, new_config):
        """
        Whenever a balancer is updated we sync all of the balancer conf files.
        """
        self.sync_balancer_files()

    def on_balancer_remove(self, name):
        """
        The removal of a load balancer config isn't supported just yet.

        If the balancer being removed is the only configured one we fire
        a critical log message saying so.  A writer setup with no balancers
        is less than useless.
        """
        if len(self.configurables[Balancer]) == 1:
            logger.critical(
                "'%s' config file removed! It was the only balancer left!",
                name
            )

    def on_discovery_add(self, discovery):
        """
        When a discovery is added we call `connect()` on it and launch a thread
        for each cluster where the discovery watches for changes to the
        cluster's nodes.
        """
        discovery.connect()

        for cluster in self.configurables[Cluster].values():
            if cluster.discovery != discovery.name:
                continue

            self.launch_thread(
                cluster.name, discovery.start_watching,
                cluster, self.sync_balancer_files
            )

        self.sync_balancer_files()

    def on_discovery_remove(self, name):
        """
        When a Discovery is removed we must make sure to call its `stop()`
        method to close any connections or do any clean up.
        """
        self.configurables[Discovery][name].stop()

        self.sync_balancer_files()

    def on_cluster_add(self, cluster):
        """
        Once a cluster is added we tell its associated discovery method to
        start watching for changes to the cluster's child nodes (if the
        discovery method is configured and available).
        """
        if cluster.discovery not in self.configurables[Discovery]:
            return

        discovery = self.configurables[Discovery][cluster.discovery]

        self.launch_thread(
            cluster.name, discovery.start_watching,
            cluster, self.sync_balancer_files
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
        `sync_balancer_files` method is called.
        """
        cluster = self.configurables[Cluster][name]

        old_discovery = cluster.discovery
        new_discovery = new_config["discovery"]
        if old_discovery == new_discovery:
            self.sync_balancer_files()
            return

        logger.info(
            "Switching '%s' cluster discovery from '%s' to '%s'",
            name, old_discovery, new_discovery
        )

        if old_discovery in self.configurables[Discovery]:
            self.configurables[Discovery][old_discovery].stop_watching(
                cluster
            )
            self.kill_thread(cluster.name)
        if new_discovery not in self.configurables[Discovery]:
            logger.warn(
                "New discovery '%s' for cluster '%s' is unknown/unavailable.",
                new_discovery, name
            )
            self.sync_balancer_files()
            return

        discovery = self.configurables[Discovery][new_discovery]
        self.launch_thread(
            cluster.name,
            discovery.start_watching, cluster, self.sync_balancer_files
        )

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
            self.kill_thread(name)

        self.sync_balancer_files()

    def wind_down(self):
        """
        Winding down a writer ConfigWatcher is merely a matter of stopping
        the present discovery methods.
        """
        for discovery in self.configurables[Discovery].values():
            discovery.stop()
