try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import Mock, patch

from lighthouse.haproxy.config import HAProxyConfig


class HAProxyConfigTests(unittest.TestCase):

    @patch("lighthouse.haproxy.config.datetime")
    def test_generate_includes_timestamp(self, mock_datetime):
        config = HAProxyConfig(
            Mock("global"), Mock("default"),
        )

        self.assertTrue(
            str(mock_datetime.datetime.now.return_value.strftime.return_value)
            in config.generate([])
        )

    @patch("lighthouse.haproxy.config.Section")
    def test_includes_global_and_defaults_stanzas(self, Section):
        included_stanzas = []

        def add_included_stanzas(heading, *stanzas):
            included_stanzas.extend(stanzas)

        Section.side_effect = add_included_stanzas

        global_stanza = Mock("global")
        defaults_stanza = Mock("defaults")

        config = HAProxyConfig(global_stanza, defaults_stanza, None)

        config.generate([])

        self.assertIn(global_stanza, included_stanzas)
        self.assertIn(defaults_stanza, included_stanzas)

    @patch("lighthouse.haproxy.config.PeersStanza")
    @patch("lighthouse.haproxy.config.BackendStanza")
    @patch("lighthouse.haproxy.config.FrontendStanza")
    @patch("lighthouse.haproxy.config.Section")
    def test_includes_frontend_backend_and_peers(self, Section,
                                                 FrontendStanza,
                                                 BackendStanza,
                                                 PeersStanza):
        included_stanzas = []

        def add_included_stanzas(heading, *stanzas):
            included_stanzas.extend(stanzas)

        Section.side_effect = add_included_stanzas

        global_stanza = Mock(name="global")
        defaults_stanza = Mock(name="defaults")

        config = HAProxyConfig(global_stanza, defaults_stanza)

        cluster1 = Mock(haproxy={"acl": "path_beg /api"})
        cluster1_backend = Mock(name="cluster1_backend")
        cluster1_peers = Mock(name="cluster1_peers")
        cluster2 = Mock(haproxy={"port": 8000})
        cluster2_frontend = Mock(name="cluster2_frontend")
        cluster2_backend = Mock(name="cluster2_backend")
        cluster2_peers = Mock(name="cluster2_peers")

        frontend_stanzas = [cluster2_frontend]
        backend_stanzas = [cluster1_backend, cluster2_backend]
        peers_stanzas = [cluster1_peers, cluster2_peers]

        def get_frontend_stanza(cluster, bind_address=None):
            return frontend_stanzas.pop(0)

        FrontendStanza.side_effect = get_frontend_stanza

        def get_backend_stanza(cluster):
            return backend_stanzas.pop(0)

        BackendStanza.side_effect = get_backend_stanza

        def get_peers_stanza(cluster):
            return peers_stanzas.pop(0)

        PeersStanza.side_effect = get_peers_stanza

        config.generate([cluster1, cluster2], version=(1, 5, 12))

        self.assertEqual(
            included_stanzas,
            [
                global_stanza, defaults_stanza,
                cluster2_frontend,  # cluster1 FE skipped, it's ACL
                cluster1_backend, cluster2_backend,
                cluster1_peers, cluster2_peers
            ]
        )

    @patch("lighthouse.haproxy.config.PeersStanza")
    @patch("lighthouse.haproxy.config.BackendStanza")
    @patch("lighthouse.haproxy.config.FrontendStanza")
    @patch("lighthouse.haproxy.config.Section")
    def test_excludes_peers_stanzas_in_older_versions(self, Section,
                                                      FrontendStanza,
                                                      BackendStanza,
                                                      PeersStanza):
        included_stanzas = []

        def add_included_stanzas(heading, *stanzas):
            included_stanzas.extend(stanzas)

        Section.side_effect = add_included_stanzas

        global_stanza = Mock()
        defaults_stanza = Mock()

        config = HAProxyConfig(global_stanza, defaults_stanza)

        cluster1 = Mock(haproxy={"port": 9999})
        cluster1_frontend = Mock()
        cluster1_backend = Mock()
        cluster1_peers = Mock()
        cluster2 = Mock(haproxy={"port": 8888})
        cluster2_frontend = Mock()
        cluster2_backend = Mock()
        cluster2_peers = Mock()

        frontend_stanzas = [cluster1_frontend, cluster2_frontend]
        backend_stanzas = [cluster1_backend, cluster2_backend]
        peers_stanzas = [cluster1_peers, cluster2_peers]

        def get_frontend_stanza(cluster, bind_address=None):
            return frontend_stanzas.pop(0)

        FrontendStanza.side_effect = get_frontend_stanza

        def get_backend_stanza(cluster):
            return backend_stanzas.pop(0)

        BackendStanza.side_effect = get_backend_stanza

        def get_peers_stanza(cluster):
            return peers_stanzas.pop(0)

        PeersStanza.side_effect = get_peers_stanza

        config.generate([cluster1, cluster2], version=(1, 4, 10))

        self.assertEqual(
            included_stanzas,
            [
                global_stanza, defaults_stanza,
                cluster1_frontend, cluster2_frontend,
                cluster1_backend, cluster2_backend,
            ]
        )

    def test_excludes_peers_in_older_versions(self):
        pass

    @patch("lighthouse.haproxy.config.Section")
    def test_can_include_stats_stanza(self, Section):
        included_stanzas = []

        def add_included_stanzas(heading, *stanzas):
            included_stanzas.extend(stanzas)

        Section.side_effect = add_included_stanzas

        stats_stanza = Mock("listen")

        config = HAProxyConfig(
            Mock("global"), Mock("default"), None,
        )

        config.generate([])

        self.assertNotIn(stats_stanza, included_stanzas)

        config = HAProxyConfig(
            Mock("global"), Mock("default"), stats_stanza=stats_stanza,
        )

        config.generate([])

        self.assertIn(stats_stanza, included_stanzas)
