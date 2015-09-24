import collections
import logging
import threading
import time

import six

from lighthouse.balancer import Balancer

from .config import HAProxyConfig
from .control import HAProxyControl
from .stanzas.stanza import Stanza
from .stanzas.proxy import ProxyStanza
from .stanzas.stats import StatsStanza


MIN_TIME_BETWEEN_RESTARTS = 2  # seconds

logger = logging.getLogger(__name__)


class HAProxy(Balancer):
    """
    The HAProxy balancer class.

    Leverages the HAProxy control, config and stanza-related classes in order
    to keep the HAProxy config file in sync with the services and nodes
    discovered.
    """

    name = "haproxy"

    def __init__(self, *args, **kwargs):
        super(HAProxy, self).__init__(*args, **kwargs)

        self.last_restart = 0
        self.restart_required = True
        self.restart_interval = MIN_TIME_BETWEEN_RESTARTS
        self.restart_lock = threading.RLock()

        self.haproxy_config_path = None
        self.config_file = None
        self.control = None

    @classmethod
    def validate_dependencies(cls):
        """
        The HAProxy Balancer doesn't use any specific python libraries so there
        are no extra dependencies to check for.
        """
        return True

    @classmethod
    def validate_config(cls, config):
        """
        Validates that a config file path and a control socket file path
        and pid file path are all present in the HAProxy config.
        """
        if "config_file" not in config:
            raise ValueError("No config file path given")
        if "socket_file" not in config:
            raise ValueError("No control socket path given")
        if "pid_file" not in config:
            raise ValueError("No PID file path given")
        if "stats" in config and "port" not in config["stats"]:
            raise ValueError("Stats interface defined, but no port given")
        if "proxies" in config:
            cls.validate_proxies_config(config["proxies"])

        return config

    @classmethod
    def validate_proxies_config(cls, proxies):
        """
        Specific config validation method for the "proxies" portion of a
        config.

        Checks that each proxy defines a port and a list of `upstreams`,
        and that each upstream entry has a host and port defined.
        """
        for name, proxy in six.iteritems(proxies):
            if "port" not in proxy:
                raise ValueError("No port defined for proxy %s" % name)
            if "upstreams" not in proxy:
                raise ValueError(
                    "No upstreams defined for proxy %s" % name
                )
            for upstream in proxy["upstreams"]:
                if "host" not in upstream:
                    raise ValueError(
                        "No host defined for upstream in proxy %s" % name
                    )
                if "port" not in upstream:
                    raise ValueError(
                        "No port defined for upstream in proxy %s" % name
                    )

    def apply_config(self, config):
        """
        Constructs HAProxyConfig and HAProxyControl instances based on the
        contents of the config.

        This is mostly a matter of constructing the configuration stanzas.
        """
        self.haproxy_config_path = config["config_file"]

        global_stanza = Stanza("global")
        global_stanza.add_lines(config.get("global", []))
        global_stanza.add_lines([
            "stats socket %s mode 600 level admin" % config["socket_file"],
            "stats timeout 2m"
        ])

        defaults_stanza = Stanza("defaults")
        defaults_stanza.add_lines(config.get("defaults", []))

        proxy_stanzas = [
            ProxyStanza(
                name, proxy["port"], proxy["upstreams"],
                proxy.get("options", []),
                proxy.get("bind_address")
            )
            for name, proxy in six.iteritems(config.get("proxies", {}))
        ]

        stats_stanza = None
        if "stats" in config:
            stats_stanza = StatsStanza(
                config["stats"]["port"], config["stats"].get("uri", "/")
            )
            for timeout in ("client", "connect", "server"):
                if timeout in config["stats"].get("timeouts", {}):
                    stats_stanza.add_line(
                        "timeout %s %d" % (
                            timeout,
                            config["stats"]["timeouts"][timeout]
                        )
                    )

        self.config_file = HAProxyConfig(
            global_stanza, defaults_stanza,
            proxy_stanzas=proxy_stanzas, stats_stanza=stats_stanza,
            meta_clusters=config.get("meta_clusters", {}),
            bind_address=config.get("bind_address")
        )

        self.control = HAProxyControl(
            config["config_file"], config["socket_file"], config["pid_file"],
        )

    def sync_file(self, clusters):
        """
        Generates new HAProxy config file content and writes it to the
        file at `haproxy_config_path`.

        If a restart is not necessary the nodes configured in HAProxy will
        be synced on the fly.  If a restart *is* necessary, one will be
        triggered.
        """
        logger.info("Updating HAProxy config file.")
        if not self.restart_required:
            self.sync_nodes(clusters)

        version = self.control.get_version()

        with open(self.haproxy_config_path, "w") as f:
            f.write(self.config_file.generate(clusters, version=version))

        if self.restart_required:
            with self.restart_lock:
                self.restart()

    def restart(self):
        """
        Tells the HAProxy control object to restart the process.

        If it's been fewer than `restart_interval` seconds since the previous
        restart, it will wait until the interval has passed.  This staves off
        situations where the process is constantly restarting, as it is
        possible to drop packets for a short interval while doing so.
        """
        delay = (self.last_restart - time.time()) + self.restart_interval

        if delay > 0:
            time.sleep(delay)

        self.control.restart()

        self.last_restart = time.time()
        self.restart_required = False

    def sync_nodes(self, clusters):
        """
        Syncs the enabled/disabled status of nodes existing in HAProxy based
        on the given clusters.

        This is used to inform HAProxy of up/down nodes without necessarily
        doing a restart of the process.
        """
        logger.info("Syncing HAProxy backends.")

        current_nodes, enabled_nodes = self.get_current_nodes(clusters)

        for cluster_name, nodes in six.iteritems(current_nodes):
            for node in nodes:
                if node["svname"] in enabled_nodes[cluster_name]:
                    command = self.control.enable_node
                else:
                    command = self.control.disable_node

                try:
                    response = command(cluster_name, node["svname"])
                except Exception:
                    logger.exception("Error when enabling/disabling node")
                    self.restart_required = True
                else:
                    if response:
                        logger.error(
                            "Socket command for %s node %s failed: %s",
                            cluster_name, node["svname"], response
                        )
                        self.restart_required = True
                        return

        logger.info("HAProxy nodes/servers synced.")

    def get_current_nodes(self, clusters):
        """
        Returns two dictionaries, the current nodes and the enabled nodes.

        The current_nodes dictionary is keyed off of the cluster name and
        values are a list of nodes known to HAProxy.

        The enabled_nodes dictionary is also keyed off of the cluster name
        and values are list of *enabled* nodes, i.e. the same values as
        current_nodes but limited to servers currently taking traffic.
        """
        current_nodes = self.control.get_active_nodes()
        enabled_nodes = collections.defaultdict(list)

        for cluster in clusters:
            if not cluster.nodes:
                continue

            if cluster.name not in current_nodes:
                logger.debug(
                    "New cluster '%s' added, restart required.",
                    cluster.name
                )
                self.restart_required = True

            for node in cluster.nodes:
                if node.name not in [
                        current_node["svname"]
                        for current_node in current_nodes.get(cluster.name, [])
                ]:
                    logger.debug(
                        "New node added to cluster '%s', restart required.",
                        cluster.name
                    )
                    self.restart_required = True

                enabled_nodes[cluster.name].append(node.name)

        return current_nodes, enabled_nodes
