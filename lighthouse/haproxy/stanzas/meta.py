import logging

from .stanza import Stanza


logger = logging.getLogger(__name__)


class MetaFrontendStanza(Stanza):
    """
    Stanza subclass representing a shared "meta" cluster frontend.

    These frontends just contain ACL directives for routing requests to
    separate cluster backends.  If a member cluster does not have an ACL rule
    defined in its haproxy config an error is logged and the member cluster
    is skipped.
    """

    def __init__(self, name, port, lines, members, bind_address=None):
        super(MetaFrontendStanza, self).__init__("frontend")
        self.header = "frontend %s" % name

        if not bind_address:
            bind_address = ""

        self.add_line("bind %s:%s" % (bind_address, port))
        self.add_lines(lines)

        for cluster in members:
            if "acl" not in cluster.haproxy:
                logger.error(
                    "Cluster %s is part of meta-cluster %s," +
                    " but no acl rule defined.",
                    cluster.name, name
                )
                continue
            self.add_lines([
                "acl is_%s %s" % (cluster.name, cluster.haproxy["acl"]),
                "use_backend %s if is_%s" % (cluster.name, cluster.name)
            ])
