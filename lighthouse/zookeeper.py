import logging
import threading

from kazoo import client, exceptions

from lighthouse.discovery import Discovery
from lighthouse.node import Node
from lighthouse.events import wait_on_event


DEFAULT_CONNECT_TIMEOUT = 30  # seconds
NO_NODE_INTERVAL = 2  # seconds


logger = logging.getLogger(__name__)


class ZookeeperDiscovery(Discovery):
    """
    The Zookeeper-based discovery method.

    This is the discovery method included with lighthouse and the most
    recommended one as Zookeeper is one of the most solid CP systems available.

    Cluster nodes are denoted as up or down based on the existence of
    associated znodes.  If a node is up and available, the znode with the
    path <base_path>/<service_name>/<node_name> will exist and the data on
    the znode is the serialized representation of the cluster node.

    These znodes are ephemeral, so that if the lighthouse reporter reporting
    on the node goes down (i.e. the machine they are on goes down), the znode
    will disappear and lighthouse writers will update accordingly.
    """

    name = "zookeeper"

    def __init__(self, *args, **kwargs):
        super(ZookeeperDiscovery, self).__init__(*args, **kwargs)

        self.hosts = []
        self.base_path = None

        self.client = None
        self.connected = False

        self.nodes_updated = None
        self.stop_events = {}
        self.watched_clusters = set()

    @classmethod
    def validate_dependencies(cls):
        """
        Since the Zookeeper discovery method and its `kazoo` library dependency
        is included by default, this method does nothing and just returns True.
        """
        return True

    @classmethod
    def validate_config(cls, config):
        """
        Validates that a list of hosts and a base path to watch are configured.
        """
        if "hosts" not in config:
            raise ValueError("Missing discovery option 'hosts'")
        if "path" not in config:
            raise ValueError("Missing discovery option 'path'")

    def apply_config(self, config):
        """
        Takes the given config dictionary and sets the hosts and base_path
        and connection_timeout (optional in the config) attributes.

        If the kazoo client connection is established, its hosts list is
        updated to the newly configured value.
        """
        self.hosts = config["hosts"]
        old_base_path = self.base_path
        self.base_path = config["path"]
        self.connect_timeout = config.get(
            "connect_timeout", DEFAULT_CONNECT_TIMEOUT
        )
        if not self.connected:
            return

        self.client.set_hosts(",".join(self.hosts))

        if old_base_path and old_base_path != self.base_path:
            clusters = self.watched_clusters.copy()
            for cluster in clusters:
                self.stop_watching(cluster, base_path=old_base_path)
                self.start_watching(cluster)
            clusters.clear()

    def connect(self):
        """
        Creates a new KazooClient and establishes a connection.

        Passes the client the `handle_connection_change` method as a callback
        to fire when the Zookeeper connection changes state.
        """
        self.client = client.KazooClient(
            hosts=",".join(self.hosts),
        )
        self.client.start(timeout=self.connect_timeout)
        self.connected = True
        self.client.add_listener(self.handle_connection_change)

    def disconnect(self):
        """
        Removes any references to ChildWatch instances and stops and closes
        the kazoo connection.
        """
        logger.info("Disconnecting from Zookeeper.")
        self.client.stop()
        self.client.close()

    def handle_connection_change(self, state):
        """
        Callback for handling changes in the kazoo client's connection state.

        If the connection becomes lost or suspended, the `connected` attribute
        is set to False.  Other given states imply that the connection is
        established so `connected` is set to True.
        """
        if state == client.KazooState.LOST:
            if not self.shutdown.is_set():
                logger.warn("Zookeeper session lost!")
            self.connected = False
        elif state == client.KazooState.SUSPENDED:
            logger.warn("Zookeeper connection suspended!")
            self.connected = False
        else:
            logger.info("Zookeeper connection (re)established.")
            self.connected = True

    def start_watching(self, cluster):
        """
        Launches a greenlet to asynchronously watch a cluster's associated
        znode.

        Also adds the cluster to the `watched_clusters` set so that any calls
        to `apply_config` re-watch the cluster appropriately.
        """
        self.watched_clusters.add(cluster)
        watcher_thread = threading.Thread(
            name="zookeeper",
            target=self.launch_child_watcher, args=(cluster,)
        )
        watcher_thread.daemon = True
        watcher_thread.start()

    def launch_child_watcher(self, cluster):
        """
        Initiates the "watching" of a cluster's associated znode.

        This is done via kazoo's ChildrenWatch object.  When a cluster's
        znode's child nodes are updated, a callback is fired and we update
        the cluster's `nodes` attribute based on the existing child znodes
        and set the `nodes_updated` Event.

        If the cluster's znode does not exist we wait for `NO_NODE_INTERVAL`
        seconds before trying again as long as no ChildrenWatch exists for
        the given cluster yet and we are not in the process of shutting down.
        """
        cluster_node_path = "/".join([self.base_path, cluster.name])

        self.stop_events[cluster_node_path] = threading.Event()

        def should_stop():
            return (
                cluster_node_path not in self.stop_events
                or self.stop_events[cluster_node_path].is_set()
            )

        def wait_for_stop(timeout=None):
            if cluster_node_path in self.stop_events:
                wait_on_event(self.stop_events[cluster_node_path], timeout)

        callback = self.make_znode_callback(cluster_node_path, cluster)

        while not should_stop():
            try:
                self.client.ChildrenWatch(cluster_node_path, callback)
                wait_for_stop()
            except exceptions.NoNodeError:
                wait_for_stop(timeout=NO_NODE_INTERVAL)

    def make_znode_callback(self, path, cluster):
        """
        Helper method for generating a callback to be used in kazoo's
        ChildrenWatch feature.

        Given a znode path and a Cluster instance, the returned function
        takes a list of child znode names and iterates over each one,
        deserializing the child znode's data and updating the Cluster
        instances `nodes` attribute with the valid nodes.
        """

        def on_znode_change(children):
            if (
                    path not in self.stop_events
                    or self.stop_events[path].is_set()
            ):
                return False

            logger.debug("znode children changed! (%s)", path)

            new_nodes = []
            for child in children:
                child_path = "/".join([path, child])
                try:
                    new_nodes.append(
                        Node.deserialize(self.client.get(child_path)[0])
                    )
                except ValueError:
                    logger.exception("Invalid node at path '%s'", child)
                    continue

            cluster.nodes = new_nodes
            self.nodes_updated.set()

        return on_znode_change

    def stop_watching(self, cluster, base_path=None):
        """
        Causes the thread that launched the watch of the cluster path
        to end by setting the proper stop event found in `self.stop_events`.

        Also discards the cluster from the `watched_clusters` set so that
        any new calls to `apply_config` don't inadvertently start watching
        the cluster again.
        """
        if not base_path:
            base_path = self.base_path

        cluster_node_path = "/".join([base_path, cluster.name])
        if cluster_node_path in self.stop_events:
            self.stop_events[cluster_node_path].set()

        self.watched_clusters.discard(cluster)

    def report_up(self, service):
        """
        Report the given service's present node as up by creating/updating
        its respective znode in Zookeeper and setting the znode's data to
        the serialized representation of the node.

        If for whatever reason we are not currently connect to Zookeeper a
        warning is given and no further action is taken.
        """
        if not self.connected:
            logger.warn("Not connected to zookeeper, cannot save znode.")
            return

        node = Node.current(service)

        path = self.path_of(service, node)
        data = node.serialize().encode()

        try:
            logger.debug("Setting node value to %r", data)
            self.client.set(path, data)
        except exceptions.NoNodeError:
            logger.debug("Target znode did not exist, creating new one.")
            self.client.create(
                path, value=data,
                ephemeral=True, makepath=True
            )

    def report_down(self, service):
        """
        Reports the given service's present node as down by deleting the
        node's znode in Zookeeper if the znode is present.

        If for whatever reason we are not currently connect to Zookeeper a
        warning is given and no further action is taken.
        """
        if not self.connected:
            logger.warn("Not connected to zookeeper, cannot delete znode.")
            return

        node = Node.current(service)

        path = self.path_of(service, node)
        try:
            logger.debug("Deleting znode at %s", path)
            self.client.delete(path)
        except exceptions.NoNodeError:
            pass

    def path_of(self, service, node):
        """
        Helper method for determining the Zookeeper path for a given cluster
        member node.
        """
        return "/".join([self.base_path, service.name, node.name])
