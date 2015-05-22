from .stanza import Stanza


class FrontendStanza(Stanza):
    """
    Stanza subclass representing a "frontend" stanza.

    A frontend stanza defines an address to bind to an a backend to route
    traffic to.  A cluster can defined custom lines via a "frontend" entry
    in their haproxy config dictionary.
    """

    def __init__(self, cluster, bind_address=None):
        super(FrontendStanza, self).__init__("frontend")
        self.header = "frontend %s" % cluster.name

        if not bind_address:
            bind_address = ""

        self.add_lines(cluster.haproxy.get("frontend", []))
        self.add_line("bind %s:%s" % (bind_address, cluster.haproxy["port"]))
        self.add_line("default_backend %s" % cluster.name)
