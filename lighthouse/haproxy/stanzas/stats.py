from .stanza import Stanza


class StatsStanza(Stanza):
    """
    Stanza subclass representing a "listen" stanza specifically for the
    HAProxy stats feature.

    Takes an optional uri parameter that defaults to the root uri.
    """

    def __init__(self, port, uri="/"):
        super(StatsStanza, self).__init__("listen")
        self.header = "listen stats :" + str(port)

        self.add_lines([
            "mode http",
            "stats enable",
            "stats uri " + uri,
        ])
