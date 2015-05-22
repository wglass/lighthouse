try:
    import unittest2 as unittest
except ImportError:
    import unittest

from lighthouse.haproxy.stanzas.proxy import ProxyStanza


class ProxyStanzaTests(unittest.TestCase):

    def test_optional_bind_address(self):
        stanza = ProxyStanza("payserver", 2222, [], bind_address="0.0.0.0")

        self.assertEqual(stanza.header, "listen payserver")
        self.assertIn("bind 0.0.0.0:2222", stanza.lines)

    def test_optional_lines(self):
        stanza = ProxyStanza(
            "payserver", 2222, [], options=["mode http", "maxconn 400"]
        )

        self.assertIn("mode http", stanza.lines)
        self.assertIn("maxconn 400", stanza.lines)

    def test_upstream_entries(self):
        stanza = ProxyStanza(
            "payserver", 2222,
            [
                {"host": "api.partner.com", "port": 88},
                {"host": "b2b.other.com", "port": 800, "max_conn": 500}
            ]
        )

        self.assertEqual(
            stanza.lines,
            [
                "bind :2222",
                "server api.partner.com:88 api.partner.com:88 ",
                "server b2b.other.com:800 b2b.other.com:800 maxconn 500"
            ]
        )
