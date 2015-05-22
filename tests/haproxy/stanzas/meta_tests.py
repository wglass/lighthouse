try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import Mock

from lighthouse.haproxy.stanzas.meta import MetaFrontendStanza


class MetaFrontendStanzaTests(unittest.TestCase):

    def test_custom_bind_address(self):
        cluster1 = Mock(haproxy={})
        cluster2 = Mock(haproxy={})
        stanza = MetaFrontendStanza(
            "api", 8000, [], [cluster1, cluster2],
            bind_address="127.0.0.1"
        )

        self.assertIn("bind 127.0.0.1:8000", stanza.lines)

    def test_member_cluster_acls(self):
        cluster1 = Mock(haproxy={"acl": "path_beg /api/foo"})
        cluster1.name = "foo_api"
        cluster2 = Mock(haproxy={"acl": "path_beg /api/bar"})
        cluster2.name = "bar_api"

        stanza = MetaFrontendStanza("api", 8000, [], [cluster1, cluster2])

        self.assertEqual(stanza.header, "frontend api")

        self.assertIn("acl is_foo_api path_beg /api/foo", stanza.lines)
        self.assertIn("acl is_bar_api path_beg /api/bar", stanza.lines)
        self.assertIn("use_backend foo_api if is_foo_api", stanza.lines)
        self.assertIn("use_backend bar_api if is_bar_api", stanza.lines)

    def test_member_cluster_with_no_acls(self):
        cluster1 = Mock(haproxy={"acl": "path_beg /api/foo"})
        cluster1.name = "foo_api"
        cluster2 = Mock(haproxy={})
        cluster2.name = "bar_api"

        stanza = MetaFrontendStanza("api", 8000, [], [cluster1, cluster2])

        self.assertEqual(stanza.header, "frontend api")

        self.assertNotIn("bar_api", str(stanza))

    def test_custom_config_lines(self):
        cluster1 = Mock(haproxy={})
        cluster2 = Mock(haproxy={})
        stanza = MetaFrontendStanza(
            "api", 8000, ["mode http"], [cluster1, cluster2],
        )

        self.assertIn("mode http", stanza.lines)
