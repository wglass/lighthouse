import logging

from .stanza import Stanza


logger = logging.getLogger(__name__)


class BackendStanza(Stanza):
    """
    Stanza subclass representing a "backend" stanza.

    A backend stanza defines the nodes (or "servers") belonging to a given
    cluster as well as how routing/load balancing between those nodes happens.

    A given cluster can define custom directives via a list of lines in their
    haproxy config with the key "backend".
    """

    def __init__(self, cluster):
        super(BackendStanza, self).__init__("backend")
        self.header = "backend %s" % cluster.name

        if not cluster.nodes:
            logger.warning(
                "Cluster %s has no nodes, backend stanza may be blank.",
                cluster.name
            )

        backend_lines = cluster.haproxy.get("backend", [])
        self.add_lines(backend_lines)
        for node in cluster.nodes:
            http_mode = bool("mode http" in backend_lines)
            self.add_line(
                "server %(name)s %(host)s:%(port)s %(cookie)s %(options)s" % {
                    "name": node.name,
                    "host": node.ip,
                    "port": node.port,
                    "cookie": "cookie " + node.name if http_mode else "",
                    "options": cluster.haproxy.get("server_options", "")
                }
            )
