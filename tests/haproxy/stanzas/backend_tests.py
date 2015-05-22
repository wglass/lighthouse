try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import Mock

from lighthouse.haproxy.stanzas.backend import BackendStanza


class BackendStanzaTests(unittest.TestCase):

    def test_includes_cookie_in_http_mode(self):
        http_node = Mock(host="server1.int", ip="10.0.1.12", port=8000)
        http_node.name = "server1.int:8000"

        cluster = Mock()
        cluster.name = "accounts"
        cluster.nodes = [http_node]
        cluster.haproxy = {
            "backend": [
                "mode http"
            ]
        }

        stanza = BackendStanza(cluster)

        self.assertEqual(
            str(stanza),
            """backend accounts
\tmode http
\tserver server1.int:8000 10.0.1.12:8000 cookie server1.int:8000 """
        )

    def test_no_nodes(self):
        node = Mock(host="server1.int", ip="10.0.1.12", port=8000)
        node.name = "server1.int:8000"

        cluster = Mock()
        cluster.name = "accounts"
        cluster.haproxy = {
            "backend": [
                "timeout server 2000",
            ]
        }
        cluster.nodes = []

        stanza = BackendStanza(cluster)

        self.assertEqual(
            str(stanza),
            """backend accounts
\ttimeout server 2000"""
        )

    def test_custom_backend_lines(self):
        node = Mock(host="server1.int", ip="10.0.1.12", port=8000)
        node.name = "server1.int:8000"

        cluster = Mock()
        cluster.name = "accounts"
        cluster.haproxy = {
            "backend": [
                "timeout server 2000",
                "fee foo fi",  # skipped as invalid
            ]
        }
        cluster.nodes = [node]

        stanza = BackendStanza(cluster)

        self.assertEqual(
            str(stanza),
            """backend accounts
\ttimeout server 2000
\tserver server1.int:8000 10.0.1.12:8000  """
        )

    def test_tcp_mode(self):
        tcp_node = Mock(host="server1.int", ip="10.0.1.12", port=8000)
        tcp_node.name = "server1.int:8000"

        cluster = Mock()
        cluster.name = "redis_cache"
        cluster.nodes = [tcp_node]
        cluster.haproxy = {
            "backend": [
                "mode tcp"
            ]
        }

        stanza = BackendStanza(cluster)

        self.assertEqual(
            str(stanza),
            """backend redis_cache
\tmode tcp
\tserver server1.int:8000 10.0.1.12:8000  """
        )
