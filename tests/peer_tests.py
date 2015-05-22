try:
    import unittest2 as unittest
except ImportError:
    import unittest

import json

from mock import patch

from lighthouse.peer import Peer


class PeerTests(unittest.TestCase):

    def test_default_port(self):
        peer = Peer("service02", "1.2.3.4")

        self.assertEqual(peer.port, 1024)

    @patch("lighthouse.peer.socket")
    def test_current_uses_local_machine_values(self, mock_socket):
        mock_socket.getfqdn.return_value = "my-host.example.co.biz"
        mock_socket.gethostbyname.return_value = "10.10.10.1"

        peer = Peer.current()

        self.assertEqual(peer.name, "my-host.example.co.biz")
        self.assertEqual(peer.ip, "10.10.10.1")

        mock_socket.gethostbyname.assert_called_once_with(
            "my-host.example.co.biz"
        )

    def test_serialize(self):
        peer = Peer("cluster03", "196.0.0.8", port=3333)

        self.assertEqual(
            json.loads(peer.serialize()),
            {
                "name": "cluster03",
                "ip": "196.0.0.8",
                "port": 3333
            }
        )

    def test_deserialize(self):
        peer = Peer.deserialize(
            json.dumps({
                "name": "cluster03",
                "ip": "196.0.0.8",
                "port": 3333
            })
        )

        self.assertEqual(peer.name, "cluster03")
        self.assertEqual(peer.ip, "196.0.0.8")
        self.assertEqual(peer.port, 3333)

    def test_deserialize_without_port(self):
        peer = Peer.deserialize(
            json.dumps({
                "name": "cluster03",
                "ip": "196.0.0.8",
            })
        )

        self.assertEqual(peer.name, "cluster03")
        self.assertEqual(peer.ip, "196.0.0.8")
        self.assertEqual(peer.port, 1024)

    def test_deserialize_without_name(self):
        self.assertRaises(
            ValueError,
            Peer.deserialize,
            json.dumps({
                "ip": "196.0.0.8",
                "port": 333
            })
        )

    def test_deserialize_without_ip(self):
        self.assertRaises(
            ValueError,
            Peer.deserialize,
            json.dumps({
                "name": "cluster03",
                "port": 333
            })
        )

    def test_equivalence(self):
        peer1 = Peer("app01", "10.0.3.10", port=8888)
        peer2 = Peer("app01.local", "10.0.3.10", port=8888)
        peer3 = Peer("app02", "10.0.3.9", port=8888)

        self.assertEqual(peer1, peer2)
        self.assertNotEqual(peer1, peer3)
        self.assertNotEqual(peer2, peer3)

    def test_set_of_peers(self):
        peer1 = Peer("app01", "10.0.3.10", port=8888)
        peer2 = Peer("app01.local", "10.0.3.10", port=8888)
        peer3 = Peer("app02", "10.0.3.9", port=8888)

        self.assertEqual(
            set([peer1, peer2, peer3]),
            set([peer1, peer3]),
        )
