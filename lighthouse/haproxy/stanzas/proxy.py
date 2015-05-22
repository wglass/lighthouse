from .stanza import Stanza


class ProxyStanza(Stanza):
    """
    Stanza for independent proxy directives.

    These are used to add simple proxying to a system, e.g. communicating
    with a third party service via a dedicated internal machine with a white-
    listed IP.
    """

    def __init__(self, name, port, upstreams, options=None, bind_address=None):
        super(ProxyStanza, self).__init__("listen")
        self.header = "listen " + name

        if not bind_address:
            bind_address = ""

        self.add_line("bind %s:%s" % (bind_address, port))

        if options:
            self.add_lines(options)

        for upstream in upstreams:
            max_conn = ""
            if "max_conn" in upstream:
                max_conn = "maxconn " + str(upstream["max_conn"])

            self.add_line(
                "server %(name)s %(name)s %(maxconn)s" % {
                    "name": ":".join(
                        [upstream["host"], str(upstream["port"])]
                    ),
                    "maxconn": max_conn
                }
            )
