try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import Mock, call, patch

from lighthouse.balancer import Balancer
from lighthouse.cluster import Cluster
from lighthouse.discovery import Discovery
from lighthouse.writer import Writer


class WriterTests(unittest.TestCase):

    @patch("lighthouse.writer.wait_on_event")
    def test_run_waits_on_shutdown(self, wait_on_event):
        writer = Writer("/etc/configs")
        writer.nodes_updated = Mock()
        writer.shutdown = Mock()

        writer.run()

        wait_on_event.assert_called_once_with(writer.shutdown)

    @patch("lighthouse.writer.wait_on_any")
    def test_update_loop_syncs_file_if_nodes_updated_set(self, wait_on_any):
        writer = Writer("/etc/configs")

        writer.nodes_updated = Mock()
        writer.shutdown = Mock()

        state = {"loops": 0, "shutdown_event_set": False}

        def mock_is_set():
            return state["shutdown_event_set"]

        def mock_wait(*events):
            state["loops"] += 1
            if state["loops"] > 1:
                state["shutdown_event_set"] = True

        writer.shutdown.is_set.side_effect = mock_is_set
        wait_on_any.side_effect = mock_wait

        writer.nodes_updated.is_set.return_value = True

        balancer = Mock()
        balancer.name = "balancer"

        cluster1 = Mock()
        cluster2 = Mock()
        writer.add_configurable(Cluster, "cache", cluster1)
        writer.add_configurable(Cluster, "app", cluster2)

        writer.add_configurable(Balancer, "balancer", balancer)

        writer.wait_for_updates()

        args, kwargs = writer.configurables[Balancer][
            "balancer"
        ].sync_file.call_args
        self.assertEqual(set(args[0]), set([cluster1, cluster2]))

        writer.nodes_updated.clear.assert_called_once_with()

    def test_add_balancer_sets_nodes_updated_flag(self):
        writer = Writer("/etc/lighthouse")
        writer.nodes_updated = Mock()

        writer.add_configurable(Balancer, "balancer", Mock())

        writer.nodes_updated.set.assert_called_once_with()

    def test_update_balancer_sets_nodes_updated_flag(self):
        writer = Writer("/etc/lighthouse")
        writer.nodes_updated = Mock()

        writer.configurables[Balancer] = {
            "balance": Mock()
        }

        writer.update_configurable(Balancer, "balance", {})

        writer.nodes_updated.set.assert_called_once_with()

    @patch("lighthouse.writer.logger")
    def test_remove_balancer_logs_critical_if_none_left(self, mock_logger):
        writer = Writer("/etc/lighthouse")
        writer.nodes_updated = Mock()

        writer.configurables[Balancer] = {
            "balance": Mock()
        }

        writer.remove_configurable(Balancer, "balance")

        self.assertEqual(mock_logger.critical.called, True)

    def test_add_discovery_calls_connect_and_sets_nodes_updated(self):
        discovery = Mock()
        discovery.name = "existing"
        discovery.nodes_updated = None

        writer = Writer("/etc/configs")

        self.assertEqual(writer.configurables[Discovery], {})

        writer.add_configurable(Discovery, "existing", discovery)

        discovery.connect.assert_called_once_with()
        self.assertEqual(discovery.nodes_updated, writer.nodes_updated)

        self.assertEqual(
            writer.configurables[Discovery],
            {
                "existing": discovery
            }
        )

    def test_add_discovery_watches_each_cluster(self):
        discovery = Mock()
        discovery.name = "existing"

        cluster1 = Mock()
        cluster1.discovery = "foobar"  # skipped
        cluster2 = Mock()
        cluster2.discovery = "existing"
        cluster3 = Mock()
        cluster3.discovery = "existing"

        writer = Writer("/etc/configs")

        writer.add_configurable(Cluster, "cache", cluster1)
        writer.add_configurable(Cluster, "app", cluster2)

        writer.add_configurable(Discovery, "existing", discovery)

        writer.add_configurable(Cluster, "web", cluster3)

        discovery.start_watching.assert_has_calls([
            call(cluster2),
            call(cluster3),
        ])

    def test_update_cluster_switches_discoveries(self):
        riak_discovery = Mock()
        riak_discovery.name = "riak"
        dns_discovery = Mock()
        dns_discovery.name = "dns"

        cluster = Mock()
        cluster.name = "app"
        cluster.discovery = "riak"
        cluster.config = {"discovery": "riak"}

        writer = Writer("/etc/configs")

        writer.add_configurable(Cluster, "app", cluster)

        writer.add_configurable(Discovery, "riak", riak_discovery)
        writer.add_configurable(Discovery, "dns", dns_discovery)

        writer.update_configurable(Cluster, cluster.name, {"discovery": "dns"})

        riak_discovery.stop_watching.assert_called_once_with(cluster)
        dns_discovery.start_watching.assert_called_once_with(cluster)

    def test_update_cluster_to_unknown_discovery(self):
        riak_discovery = Mock()
        riak_discovery.name = "riak"
        dns_discovery = Mock()
        dns_discovery.name = "dns"

        cluster = Mock()
        cluster.name = "app"
        cluster.discovery = "riak"
        cluster.config = {"discovery": "riak"}

        writer = Writer("/etc/configs")

        writer.add_configurable(Cluster, "app", cluster)

        writer.add_configurable(Discovery, "riak", riak_discovery)
        writer.add_configurable(Discovery, "dns", dns_discovery)

        writer.update_configurable(
            Cluster, cluster.name, {"discovery": "unknown"}
        )

        riak_discovery.stop_watching.assert_called_once_with(cluster)
        self.assertEqual(writer.nodes_updated.is_set(), True)
        self.assertEqual(dns_discovery.start_watching.called, False)

    def test_update_cluster_with_same_discovery(self):
        riak_discovery = Mock()
        riak_discovery.name = "riak"
        dns_discovery = Mock()
        dns_discovery.name = "dns"

        cluster = Mock()
        cluster.name = "app"
        cluster.discovery = "riak"
        cluster.config = {"discovery": "riak"}

        writer = Writer("/etc/configs")

        writer.add_configurable(Cluster, "app", cluster)

        writer.add_configurable(Discovery, "riak", riak_discovery)
        writer.add_configurable(Discovery, "dns", dns_discovery)

        writer.update_configurable(
            Cluster, cluster.name, {"discovery": "riak"}
        )

        self.assertEqual(writer.nodes_updated.is_set(), True)
        self.assertEqual(riak_discovery.stop_watching.called, False)
        self.assertEqual(dns_discovery.start_watching.called, False)

    def test_remove_cluster_stops_discovery_watch(self):
        riak_discovery = Mock()
        riak_discovery.name = "riak"

        cluster = Mock()
        cluster.name = "app"
        cluster.discovery = "riak"
        cluster.config = {"discovery": "riak"}

        writer = Writer("/etc/configs")

        writer.add_configurable(Cluster, "app-8000", cluster)

        writer.add_configurable(Discovery, "riak", riak_discovery)

        writer.remove_configurable(Cluster, "app-8000")

        riak_discovery.stop_watching.assert_called_once_with(cluster)

    def test_wind_down_stops_discoveries(self):
        discovery = Mock()
        discovery.name = "existing"

        writer = Writer("/etc/configs")

        writer.configurables[Discovery] = {
            "existing": discovery
        }

        writer.wind_down()

        discovery.stop.assert_called_once_with()

    def test_removing_discovery_calls_stop(self):
        discovery = Mock()
        discovery.name = "existing"

        writer = Writer("/etc/configs")

        writer.configurables[Discovery] = {
            "existing": discovery
        }

        writer.remove_configurable(Discovery, "existing")

        discovery.stop.assert_called_once_with()
