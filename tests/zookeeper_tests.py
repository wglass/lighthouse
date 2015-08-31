try:
    import unittest2 as unittest
except ImportError:
    import unittest

import json

from mock import patch, Mock

from kazoo import client, exceptions

from lighthouse.zookeeper import ZookeeperDiscovery


@patch("lighthouse.zookeeper.client")
class ZookeeperTests(unittest.TestCase):

    def test_validate_dependencies(self, mock_client):
        self.assertEqual(ZookeeperDiscovery.validate_dependencies(), True)

    def test_host_and_path_attributes(self, mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )

        self.assertEqual(zk.hosts, ["zk01.int", "zk02.int"])
        self.assertEqual(zk.base_path, "/lighthouse")

    def test_config_with_no_hosts(self, mock_client):
        self.assertRaises(
            ValueError,
            ZookeeperDiscovery.validate_config, {"path": "/lighthouse"}
        )

    def test_config_with_no_path(self, mock_client):
        self.assertRaises(
            ValueError,
            ZookeeperDiscovery.validate_config,
            {"hosts": ["zk01.int", "zk02.int"]}
        )

    def test_not_connected_by_default(self, mock_client):
        zk = ZookeeperDiscovery()

        self.assertEqual(zk.connected, False)

    def test_connect_via_kazoo_client(self, mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )

        zk.connect()

        self.assertEqual(zk.connected, True)

        self.assertEqual(zk.client, mock_client.KazooClient.return_value)

        mock_client.KazooClient.assert_called_once_with(
            hosts="zk01.int,zk02.int"
        )
        zk.client.start.assert_called_once_with(timeout=30)
        zk.client.add_listener.assert_called_once_with(
            zk.handle_connection_change
        )

    def test_connect_with_custom_timeout(self, mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {
                "hosts": ["zk01.int", "zk02.int"],
                "path": "/lighthouse",
                "connect_timeout": 20
            }
        )

        zk.connect()

        zk.client.start.assert_called_once_with(timeout=20)

    def test_apply_config_alters_hosts_and_path(self, mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )

        self.assertEqual(zk.hosts, ["zk01.int", "zk02.int"])
        self.assertEqual(zk.base_path, "/lighthouse")

        zk.connect()

        zk.apply_config({
            "hosts": ["zk02.int", "zk03.int"], "path": "/services"
        })

        self.assertEqual(zk.hosts, ["zk02.int", "zk03.int"])
        self.assertEqual(zk.base_path, "/services")

    def test_apply_config_updates_kazoo_hosts(self, mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )

        self.assertEqual(zk.hosts, ["zk01.int", "zk02.int"])
        self.assertEqual(zk.base_path, "/lighthouse")

        zk.connect()

        zk.apply_config({
            "hosts": ["zk02.int", "zk03.int"], "path": "/services"
        })

        zk.client.set_hosts.assert_called_once_with(
            "zk02.int,zk03.int"
        )

    def test_handle_connection_lost(self, mock_client):
        mock_client.KazooState = client.KazooState

        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )
        zk.connect()

        self.assertEqual(zk.connected, True)

        zk.handle_connection_change(client.KazooState.LOST)

        self.assertEqual(zk.connected, False)

    def test_handle_connection_lost_shutdown_set(self, mock_client):
        mock_client.KazooState = client.KazooState

        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )

        zk.connect()

        self.assertEqual(zk.connected, True)

        zk.shutdown.set()

        zk.handle_connection_change(client.KazooState.LOST)

        self.assertEqual(zk.connected, False)

    def test_handle_connection_suspended(self, mock_client):
        mock_client.KazooState = client.KazooState

        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )

        zk.connect()

        self.assertEqual(zk.connected, True)

        zk.handle_connection_change(client.KazooState.SUSPENDED)

        self.assertEqual(zk.connected, False)

    def test_handle_connection_reestablished(self, mock_client):
        mock_client.KazooState = client.KazooState

        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )

        zk.connect()

        self.assertEqual(zk.connected, True)

        zk.handle_connection_change(client.KazooState.LOST)

        self.assertEqual(zk.connected, False)

        zk.handle_connection_change(client.KazooState.CONNECTED)

        self.assertEqual(zk.connected, True)

    def test_disconnect_stops_and_closes_client(self, mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )

        zk.connect()

        zk.disconnect()

        zk.client.stop.assert_called_once_with()
        zk.client.close.assert_called_once_with()

    def test_report_up_not_connected(self, mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )

        zk.connect()

        zk.connected = False

        zk.report_up(Mock(), 8888)

        self.assertEqual(zk.client.set.called, False)

    @patch("lighthouse.peer.socket")
    @patch("lighthouse.node.socket")
    def test_report_up(self, mock_socket, peer_socket, mock_client):
        mock_socket.getfqdn.return_value = "redis1.int.local"
        mock_socket.gethostbyname.return_value = "10.0.1.8"
        peer_socket.getfqdn.return_value = "redis1.int.local"
        peer_socket.gethostbyname.return_value = "10.0.1.8"

        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )
        zk.connect()

        znode = Mock(owner_session_id="0x1234")
        zk.client.exists.return_value = znode
        zk.client.client_id = (znode.owner_session_id, "asf")

        service = Mock(metadata={"type": "master"})
        service.name = "webcache"

        zk.report_up(service, 6379)

        set_args, set_kwargs = zk.client.set.call_args

        path, data = set_args

        data = json.loads(data.decode())
        data["peer"] = json.loads(data["peer"])
        data["metadata"] = json.loads(data["metadata"])

        self.assertEqual(path, "/lighthouse/webcache/redis1.int.local:6379")
        self.assertEqual(
            data,
            {
                "host": "redis1.int.local",
                "ip": "10.0.1.8",
                "port": 6379,
                "metadata": {"type": "master"},
                "peer": {
                    "port": 1024,
                    "name": "redis1.int.local",
                    "ip": "10.0.1.8"
                }
            }
        )

    @patch("lighthouse.peer.socket")
    @patch("lighthouse.node.socket")
    def test_report_up__no_node(self, mock_socket, peer_socket, mock_client):
        mock_socket.getfqdn.return_value = "redis1.int.local"
        mock_socket.gethostbyname.return_value = "10.0.1.8"
        peer_socket.getfqdn.return_value = "redis1.int.local"
        peer_socket.gethostbyname.return_value = "10.0.1.8"

        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )
        zk.connect()

        zk.client.exists.return_value = None

        service = Mock(metadata={})
        service.name = "webcache"

        zk.report_up(service, 6379)

        self.assertEqual(zk.client.create.call_count, 1)
        create_args, create_kwargs = zk.client.create.call_args

        self.assertEqual(
            create_args,
            ("/lighthouse/webcache/redis1.int.local:6379",)
        )
        self.assertEqual(len(create_kwargs), 3)
        self.assertEqual(create_kwargs["makepath"], True)
        self.assertEqual(create_kwargs["ephemeral"], True)

        value = json.loads(create_kwargs["value"].decode())
        value["peer"] = json.loads(value["peer"])
        value["metadata"] = json.loads(value["metadata"])

        self.assertEqual(
            value,
            {
                "host": "redis1.int.local",
                "ip": "10.0.1.8",
                "port": 6379,
                "metadata": {},
                "peer": {
                    "port": 1024,
                    "name": "redis1.int.local",
                    "ip": "10.0.1.8",
                }
            }
        )

    @patch("lighthouse.peer.socket")
    @patch("lighthouse.node.socket")
    def test_report_up__old_node(self, mock_socket, peer_socket, mock_client):
        mock_socket.getfqdn.return_value = "redis1.int.local"
        mock_socket.gethostbyname.return_value = "10.0.1.8"
        peer_socket.getfqdn.return_value = "redis1.int.local"
        peer_socket.gethostbyname.return_value = "10.0.1.8"

        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )
        zk.connect()

        znode = Mock(owner_session_id="0x1234")
        zk.client.exists.return_value = znode
        zk.client.client_id = ("0xasdf", "asf")

        service = Mock(metadata={})
        service.name = "webcache"

        zk.report_up(service, 6379)

        txn = zk.client.transaction.return_value

        txn.delete.assert_called_once_with(
            "/lighthouse/webcache/redis1.int.local:6379"
        )
        create_args, create_kwargs = txn.create.call_args
        self.assertEqual(
            create_args,
            ("/lighthouse/webcache/redis1.int.local:6379",)
        )
        self.assertEqual(len(create_kwargs), 2)
        self.assertEqual(create_kwargs["ephemeral"], True)

        value = json.loads(create_kwargs["value"].decode())
        value["peer"] = json.loads(value["peer"])
        value["metadata"] = json.loads(value["metadata"])

        self.assertEqual(
            value,
            {
                "host": "redis1.int.local",
                "ip": "10.0.1.8",
                "port": 6379,
                "metadata": {},
                "peer": {
                    "port": 1024,
                    "name": "redis1.int.local",
                    "ip": "10.0.1.8",
                }
            }
        )

        txn.commit.assert_called_once_with()

    def test_report_down_not_connected(self, mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )
        zk.connect()

        zk.connected = False

        service = Mock(host="redis1")
        service.name = "webcache"

        zk.report_down(service, 6379)

        self.assertEqual(zk.client.delete.called, False)

    @patch("lighthouse.node.socket")
    def test_report_down(self, mock_socket, mock_client):
        mock_socket.getfqdn.return_value = "pg01.int.local"
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )
        zk.connect()

        service = Mock()
        service.name = "userdb"

        zk.report_down(service, 5678)

        zk.client.delete.assert_called_once_with(
            "/lighthouse/userdb/pg01.int.local:5678"
        )

    def test_report_down_no_such_node(self, mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )
        zk.connect()

        zk.client.delete.side_effect = exceptions.NoNodeError

        service = Mock(host="redis1")
        service.name = "webcache"

        zk.report_down(service, 6379)

    @patch("lighthouse.zookeeper.threading")
    def test_start_watching(self, mock_threading, mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )

        cluster = Mock()

        zk.start_watching(cluster)

        mock_threading.Thread.assert_called_once_with(
            name="zookeeper", target=zk.launch_child_watcher,
            args=(cluster,)
        )
        mock_threading.Thread.return_value.start.assert_called_once_with()

    def test_stop_watching(self, mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )

        zk.watchers = {
            "redis": Mock(),
            "webapp": Mock()
        }

        cluster = Mock()
        cluster.name = "riak"

        zk.stop_watching(cluster)

        self.assertEqual(
            set(zk.watchers.keys()),
            set(["redis", "webapp"])
        )

    def test_stop_watching_unknown_cluster(self, mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )

        cluster1 = Mock()
        cluster1.name = "cluster1"
        cluster2 = Mock()
        cluster2.name = "cluster2"

        zk.watched_clusters = set([cluster1])

        zk.stop_watching(cluster2)

        self.assertEqual(zk.watched_clusters, set([cluster1]))

    @patch("lighthouse.zookeeper.wait_on_event")
    @patch("lighthouse.zookeeper.threading")
    def test_children_change_including_invalid_one(self,
                                                   threading,
                                                   wait_on_event,
                                                   mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )
        zk.connect()
        zk.nodes_updated = Mock()

        cluster = Mock()
        cluster.name = "webapp"

        children = ["app01:8888", "app03:8888", "app04:8888"]

        def get_child_payload(child_path):
            if child_path == "/lighthouse/webapp/app01:8888":
                return [b"some invalid string ok"]
            elif child_path == "/lighthouse/webapp/app02:8888":
                return [json.dumps(
                    {"host": "app02", "ip": "10.0.1.10", "port": "8888"}
                ).encode()]
            elif child_path == "/lighthouse/webapp/app03:8888":
                return [json.dumps(
                    {"host": "app03", "ip": "10.0.1.8", "port": "8888"}
                ).encode()]
            elif child_path == "/lighthouse/webapp/app04:8888":
                return [json.dumps({
                    "host": "app04", "ip": "10.0.1.3", "port": "8888",
                    "peer": json.dumps(
                        {"name": "app04.int", "ip": "10.0.1.3", "port": 1024}
                    ),
                }).encode()]
            else:
                raise AssertionError(
                    "Looked up unaccounted for child node: %s" % child_path
                )

        zk.client.get.side_effect = get_child_payload

        threading.Event.return_value.is_set.return_value = False

        def fire_immediately(node_path, callback):
            callback(children)
            zk.stop_events[node_path].is_set.return_value = True

        zk.client.ChildrenWatch.side_effect = fire_immediately

        zk.launch_child_watcher(cluster)

        self.assertEqual(
            zk.stop_events["/lighthouse/webapp"], threading.Event.return_value
        )

        wait_on_event.assert_called_once_with(
            zk.stop_events["/lighthouse/webapp"], None
        )

        self.assertEqual(zk.nodes_updated.set.called, True)

        self.assertEqual(len(cluster.nodes), 2)
        self.assertEqual(cluster.nodes[0].host, "app03")
        self.assertEqual(cluster.nodes[0].port, "8888")
        self.assertEqual(cluster.nodes[1].host, "app04")
        self.assertEqual(cluster.nodes[1].port, "8888")
        self.assertEqual(cluster.nodes[1].peer.name, "app04.int")
        self.assertEqual(cluster.nodes[1].peer.ip, "10.0.1.3")
        self.assertEqual(cluster.nodes[1].peer.port, 1024)

    @patch("lighthouse.zookeeper.wait_on_event")
    @patch("lighthouse.zookeeper.threading")
    def test_children_change_stop_event_set(self,
                                            threading,
                                            wait_on_event,
                                            mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )
        zk.connect()
        zk.nodes_updated = Mock()

        node1 = Mock()
        node2 = Mock()

        cluster = Mock()
        cluster.name = "webapp"
        cluster.nodes = [node1, node2]

        children = ["app01:8888", "app03:8888", "app04:8888"]

        def get_child_payload(child_path):
            return [json.dumps(
                {"host": "app02", "ip": "10.0.1.10", "port": "8888"}
            ).encode()]

        zk.client.get.side_effect = get_child_payload

        threading.Event.return_value.is_set.return_value = False

        def fire_immediately(path, callback):
            zk.stop_events[path].is_set.return_value = True
            callback(children)

        zk.client.ChildrenWatch.side_effect = fire_immediately

        zk.launch_child_watcher(cluster)

        self.assertEqual(
            zk.stop_events["/lighthouse/webapp"], threading.Event.return_value
        )

        wait_on_event.assert_called_once_with(
            zk.stop_events["/lighthouse/webapp"], None
        )

        self.assertEqual(zk.nodes_updated.set.called, False)

        self.assertEqual(cluster.nodes, [node1, node2])

    @patch("lighthouse.zookeeper.wait_on_event")
    @patch("lighthouse.zookeeper.threading")
    def test_children_missing_stop_event(self,
                                         threading,
                                         wait_on_event,
                                         mock_client):
        zk = ZookeeperDiscovery()
        zk.apply_config(
            {"hosts": ["zk01.int", "zk02.int"], "path": "/lighthouse"}
        )
        zk.connect()
        zk.nodes_updated = Mock()

        node1 = Mock()
        node2 = Mock()

        cluster = Mock()
        cluster.name = "webapp"
        cluster.nodes = [node1, node2]

        children = ["app01:8888", "app03:8888", "app04:8888"]

        def get_child_payload(child_path):
            return [json.dumps(
                {"host": "app02", "ip": "10.0.1.10", "port": "8888"}
            ).encode()]

        zk.client.get.side_effect = get_child_payload

        threading.Event.return_value.is_set.return_value = False

        def fire_immediately(path, callback):
            zk.stop_events.pop(path)
            callback(children)

        zk.client.ChildrenWatch.side_effect = fire_immediately

        zk.launch_child_watcher(cluster)

        self.assertEqual(zk.stop_events, {})

        self.assertEqual(wait_on_event.called, False)

        self.assertEqual(zk.nodes_updated.set.called, False)

        self.assertEqual(cluster.nodes, [node1, node2])
