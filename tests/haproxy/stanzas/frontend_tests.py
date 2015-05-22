try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import Mock

from lighthouse.haproxy.stanzas.frontend import FrontendStanza


class FrontendStanzaTests(unittest.TestCase):

    def test_default_bind_address_is_blank(self):
        cluster = Mock()
        cluster.name = "datastore"
        cluster.haproxy = {
            "port": 99
        }

        stanza = FrontendStanza(cluster)

        self.assertEqual(stanza.header, "frontend datastore")
        self.assertEqual(
            stanza.lines,
            [
                "bind :99",
                "default_backend datastore"
            ]
        )

    def test_custom_bind_address(self):
        cluster = Mock()
        cluster.name = "datastore"
        cluster.haproxy = {
            "port": 99
        }

        stanza = FrontendStanza(cluster, bind_address="127.0.0.1")

        self.assertEqual(
            stanza.lines,
            [
                "bind 127.0.0.1:99",
                "default_backend datastore"
            ]
        )

    def test_custom_frontend_lines(self):
        cluster = Mock()
        cluster.name = "datastore"
        cluster.haproxy = {
            "port": 99,
            "frontend": [
                "foo bar bazz",  # skipped as invalid
                "acl is_api path_beg /api",
            ]
        }

        stanza = FrontendStanza(cluster)

        self.assertEqual(
            stanza.lines,
            [
                "acl is_api path_beg /api",
                "bind :99",
                "default_backend datastore"
            ]
        )
