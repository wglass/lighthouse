import logging
import threading

from kazoo import client, exceptions

from lighthouse.discovery import Discovery
from lighthouse.node import Node
from lighthouse.events import wait_on_any


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
        self.connected = threading.Event()

        self.stop_events = {}

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
        attributes.

        If the kazoo client connection is established, its hosts list is
        updated to the newly configured value.
        """
        self.hosts = config["hosts"]
        old_base_path = self.base_path
        self.base_path = config["path"]
        if not self.connected.is_set():
            return

        logger.debug("Setting ZK hosts to %s", self.hosts)
        self.client.set_hosts(",".join(self.hosts))

        if old_base_path and old_base_path != self.base_path:
            logger.critical(
                "ZNode base path changed!" +
                " Lighthouse will need to be restarted" +
                " to watch the right znodes"
            )

    def connect(self):
        """
        Creates a new KazooClient and establishes a connection.

        Passes the client the `handle_connection_change` method as a callback
        to fire when the Zookeeper connection changes state.
        """
        self.client = client.KazooClient(hosts=",".join(self.hosts))

        self.client.add_listener(self.handle_connection_change)
        self.client.start_async()

    def disconnect(self):
        """
        Stops and closes the kazoo connection.
        """
        logger.info("Disconnecting from Zookeeper.")
        self.client.stop()
        self.client.close()

    def handle_connection_change(self, state):
        """
        Callback for handling changes in the kazoo client's connection state.

        If the connection becomes lost or suspended, the `connected` Event
        is cleared.  Other given states imply that the connection is
        established so `connected` is set.
        """
        if state == client.KazooState.LOST:
            if not self.shutdown.is_set():
                logger.info("Zookeeper session lost!")
            self.connected.clear()
        elif state == client.KazooState.SUSPENDED:
            logger.info("Zookeeper connection suspended!")
            self.connected.clear()
        else:
            logger.info("Zookeeper connection (re)established.")
            self.connected.set()

    def start_watching(self, cluster, callback):
        """
        Initiates the "watching" of a cluster's associated znode.

        This is done via kazoo's ChildrenWatch object.  When a cluster's
        znode's child nodes are updated, a callback is fired and we update
        the cluster's `nodes` attribute based on the existing child znodes
        and fire a passed-in callback with no arguments once done.

        If the cluster's znode does not exist we wait for `NO_NODE_INTERVAL`
        seconds before trying again as long as no ChildrenWatch exists for
        the given cluster yet and we are not in the process of shutting down.
        """
        logger.debug("starting to watch cluster %s", cluster.name)
        wait_on_any(self.connected, self.shutdown)
        logger.debug("done waiting on (connected, shutdown)")
        znode_path = "/".join([self.base_path, cluster.name])

        self.stop_events[znode_path] = threading.Event()

        def should_stop():
            return (
                znode_path not in self.stop_events or
                self.stop_events[znode_path].is_set() or
                self.shutdown.is_set()
            )

        while not should_stop():
            try:
                if self.client.exists(znode_path):
                    break
            except exceptions.ConnectionClosedError:
                break

            wait_on_any(
                self.stop_events[znode_path], self.shutdown,
                timeout=NO_NODE_INTERVAL
            )

        logger.debug("setting up ChildrenWatch for %s", znode_path)

        @self.client.ChildrenWatch(znode_path)
        def watch(children):
            if should_stop():
                return False

            logger.debug("znode children changed! (%s)", znode_path)

            new_nodes = []
            for child in children:
                child_path = "/".join([znode_path, child])
                try:
                    new_nodes.append(
                        Node.deserialize(self.client.get(child_path)[0])
                    )
                except ValueError:
                    logger.exception("Invalid node at path '%s'", child)
                    continue

            cluster.nodes = new_nodes

            callback()

    def stop_watching(self, cluster):
        """
        Causes the thread that launched the watch of the cluster path
        to end by setting the proper stop event found in `self.stop_events`.
        """
        znode_path = "/".join([self.base_path, cluster.name])
        if znode_path in self.stop_events:
            self.stop_events[znode_path].set()

    def report_up(self, service, port):
        """
        Report the given service's present node as up by creating/updating
        its respective znode in Zookeeper and setting the znode's data to
        the serialized representation of the node.

        Waits for zookeeper to be connected before taking any action.
        """
        wait_on_any(self.connected, self.shutdown)

        node = Node.current(service, port)

        path = self.path_of(service, node)
        data = node.serialize().encode()

        znode = self.client.exists(path)

        if not znode:
            logger.debug("ZNode at %s does not exist, creating new one.", path)
            self.client.create(path, value=data, ephemeral=True, makepath=True)
        elif znode.owner_session_id != self.client.client_id[0]:
            logger.debug("ZNode at %s not owned by us, recreating.", path)
            txn = self.client.transaction()
            txn.delete(path)
            txn.create(path, value=data, ephemeral=True)
            txn.commit()
        else:
            logger.debug("Setting node value to %r", data)
            self.client.set(path, data)

    def report_down(self, service, port):
        """
        Reports the given service's present node as down by deleting the
        node's znode in Zookeeper if the znode is present.

        Waits for the Zookeeper connection to be established before further
        action is taken.
        """
        wait_on_any(self.connected, self.shutdown)

        node = Node.current(service, port)

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
