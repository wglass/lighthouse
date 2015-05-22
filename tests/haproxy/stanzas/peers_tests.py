try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import Mock

from lighthouse.haproxy.stanzas.peers import PeersStanza


class PeersStanzaTests(unittest.TestCase):

    def test_peers(self):
        peer1 = Mock()
        peer1.name = "server1"
        peer1.ip = "192.168.0.13"
        peer1.port = "88"
        peer2 = Mock()
        peer2.name = "server2"
        peer2.ip = "192.168.0.22"
        peer2.port = "88"

        cluster = Mock()
        cluster.name = "a_cluster"
        cluster.nodes = [
            Mock(peer=peer1),
            Mock(peer=None),  # skipped
            Mock(peer=peer2),
            Mock(peer=peer1),  # duplicate, skipped
        ]

        stanza = PeersStanza(cluster)

        self.assertEqual(stanza.header, "peers a_cluster")
        self.assertEqual(
            set(stanza.lines),
            set([
                "peer server1 192.168.0.13:88",
                "peer server2 192.168.0.22:88"
            ])
        )
