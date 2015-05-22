from .stanza import Stanza


class PeersStanza(Stanza):
    """
    Stanza subclass representing a "peers" stanza.

    This stanza lists "peer" haproxy instances in a cluster, so that each
    instance can coordinate and share stick-table information.  Useful for
    tracking cluster-wide stats.
    """

    def __init__(self, cluster):
        super(PeersStanza, self).__init__("peers")
        self.header = "peers " + cluster.name

        self.add_lines([
            "peer %s %s:%s" % (peer.name, peer.ip, peer.port)
            for peer in set([node.peer for node in cluster.nodes if node.peer])
        ])
