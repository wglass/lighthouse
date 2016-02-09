import json
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from lighthouse.node import Node
from lighthouse.peer import Peer


class NodeTests(unittest.TestCase):

    def test_constructor(self):
        peer = Peer("cluster04", 8888)
        node = Node("somehost", "10.0.1.12", 1234, peer=peer)

        self.assertEqual(node.host, "somehost")
        self.assertEqual(node.ip, "10.0.1.12")
        self.assertEqual(node.port, 1234)
        assert node.peer is peer

    @patch.object(Peer, "current")
    def test_constructor_defaults_to_current_peer(self, current_peer):
        node = Node("somehost", "10.0.1.12", 1234)

        self.assertEqual(node.peer, current_peer.return_value)

        current_peer.assert_called_once_with()

    def test_name_property(self):
        node = Node("somehost", "10.0.1.13", 1234)

        self.assertEqual(node.name, "somehost:1234")

    @patch.object(Peer, "current")
    def test_serialize_to_json(self, current_peer):
        peer = Peer("service05", "10.10.10.1", 9001)
        current_peer.return_value = peer

        node = Node("somehost", "10.10.10.1", 1234)

        self.assertEqual(
            json.loads(node.serialize()),
            {
                "host": "somehost",
                "ip": "10.10.10.1",
                "port": 1234,
                "metadata": "{}",
                "peer": peer.serialize(),
            }
        )

    @patch("lighthouse.node.json")
    def test_serialize_sorts_keys(self, mock_json):
        node = Node("somehost", "10.10.10.1", 1234)

        result = node.serialize()

        self.assertEqual(result, mock_json.dumps.return_value)

        for call_args in mock_json.dumps.call_args_list:
            args, kwargs = call_args
            self.assertEqual(kwargs["sort_keys"], True)

    @patch.object(Peer, "current")
    def test_deserialize_with_no_peer(self, current_peer):
        result = Node.deserialize(
            '{"port": 80, "ip": "127.0.0.1", "host": "webapp01"}'
        )

        self.assertEqual(result.host, "webapp01")
        self.assertEqual(result.ip, "127.0.0.1")
        self.assertEqual(result.port, 80)
        self.assertEqual(result.peer, current_peer.return_value)

    def test_deserialize(self):
        result = Node.deserialize(
            '{"host": "app03", "ip": "4.4.4.4", "port": 443,' +
            ' "peer": "{' +
            '\\"name\\": \\"host04\\", \\"ip\\": \\"10.10.10.10\\"' +
            '}"}'
        )

        self.assertEqual(result.host, "app03")
        self.assertEqual(result.ip, "4.4.4.4")
        self.assertEqual(result.port, 443)
        self.assertEqual(result.peer.name, "host04")
        self.assertEqual(result.peer.ip, "10.10.10.10")

    def test_deserialize_bytes(self):
        result = Node.deserialize(
            b'{"host": "app02", "ip": "4.4.4.4", "port": 443,' +
            b' "peer": "{' +
            b'\\"name\\": \\"host04\\", \\"ip\\": \\"10.10.10.10\\"' +
            b'}"}'
        )

        self.assertEqual(result.host, "app02")
        self.assertEqual(result.ip, "4.4.4.4")
        self.assertEqual(result.port, 443)
        self.assertEqual(result.peer.name, "host04")
        self.assertEqual(result.peer.ip, "10.10.10.10")

    @patch("lighthouse.node.socket")
    def test_deserialize_no_host_uses_fqdn(self, mock_socket):
        mock_socket.gethostbyaddr.return_value = (
            "app03", "app03.int", "10.0.1.12"
        )
        result = Node.deserialize('{"ip": "10.0.1.12", "port": 8888}')

        self.assertEqual(result.host, mock_socket.get_fqdn.return_value)
        mock_socket.get_fqdn.assert_called_once_with("app03")
        mock_socket.gethostbyaddr.assert_called_once_with("10.0.1.12")

    def test_deserialize_no_ip_raises_valueerror(self):
        self.assertRaises(
            ValueError,
            Node.deserialize,
            '{"host": "localhost", "port": 8888, "service_name": "cache"}'
        )

    def test_deserialize_no_port_raises_valueerror(self):
        self.assertRaises(
            ValueError,
            Node.deserialize,
            '{"host": "localhost", "ip": "10.0.1.12", "service_name": "cache"}'
        )

    def test_equivalence(self):
        node1 = Node("localhost", "10.0.1.13", 1234)
        node2 = Node("localhost", "10.0.1.13", 1234)

        self.assertTrue(node1 == node2)

    def test_equivalence_matches_port(self):
        node1 = Node("localhost", "10.0.1.13", 1234)
        node2 = Node("localhost", "10.0.1.13", 8888)

        self.assertTrue(node1 != node2)

    def test_equivalence_matches_ip(self):
        node1 = Node("localhost", "10.0.1.13", 1234)
        node2 = Node("localhost", "10.0.2.13", 1234)

        self.assertTrue(node1 != node2)

    def test_equivalence_ignores_host(self):
        node1 = Node("localhost", "10.0.1.13", 1234)
        node2 = Node("app02", "10.0.1.13", 1234)

        self.assertTrue(node1 == node2)

    def test_equivalence_ignores_peer(self):
        peer1 = Peer("service03", "10.10.0.8")
        peer2 = Peer("service04", "10.10.0.10")

        node1 = Node("localhost", "10.0.1.13", 1234, peer=peer1)
        node2 = Node("localhost", "10.0.1.13", 1234, peer=peer2)

        self.assertTrue(node1 == node2)
