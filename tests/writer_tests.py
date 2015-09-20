try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import Mock, call, patch
from concurrent import futures

from lighthouse.balancer import Balancer
from lighthouse.cluster import Cluster
from lighthouse.discovery import Discovery
from lighthouse.writer import Writer


class WriterTests(unittest.TestCase):

    def setUp(self):
        super(WriterTests, self).setUp()

        futures_patcher = patch("lighthouse.configs.watcher.futures")
        mock_futures = futures_patcher.start()

        self.addCleanup(futures_patcher.stop)

        self.mock_work_pool = mock_futures.ThreadPoolExecutor.return_value

        def run_immediately(fn, *args, **kwargs):
            f = futures.Future()

            try:
                f.set_result(fn(*args, **kwargs))
            except Exception as e:
                f.set_exception(e)

            return f

        self.mock_work_pool.submit.side_effect = run_immediately

    def test_sync_balancer_files(self):
        writer = Writer("/etc/configs")

        balancer1 = Mock()
        balancer2 = Mock()
        cluster1 = Mock()
        cluster2 = Mock()
        writer.configurables[Balancer] = {
            "balancer1": balancer1,
            "balancer2": balancer2
        }
        writer.configurables[Cluster] = {
            "cluster1": cluster1,
            "cluster2": cluster2
        }

        writer.sync_balancer_files()

        sync_args, _ = balancer1.sync_file.call_args
        self.assertEqual(
            set(sync_args[0]), set([cluster1, cluster2])
        )
        sync_args, _ = balancer2.sync_file.call_args
        self.assertEqual(
            set(sync_args[0]), set([cluster1, cluster2])
        )

    def test_add_balancer_syncs_all_files(self):
        app_cluster = Mock()
        nginx_balancer = Mock()
        haproxy_balancer = Mock()

        writer = Writer("/etc/lighthouse")
        writer.configurables[Cluster] = {"app": app_cluster}
        writer.configurables[Balancer] = {"nginx": nginx_balancer}

        writer.add_configurable(Balancer, "haproxy", haproxy_balancer)

        args, _ = nginx_balancer.sync_file.call_args
        self.assertEqual(list(args[0]), [app_cluster])

        args, _ = haproxy_balancer.sync_file.call_args
        self.assertEqual(list(args[0]), [app_cluster])

    def test_update_balancer_syncs_all_files(self):
        app_cluster = Mock()
        nginx_balancer = Mock()
        haproxy_balancer = Mock()

        writer = Writer("/etc/lighthouse")
        writer.configurables[Cluster] = {"app": app_cluster}
        writer.configurables[Balancer] = {
            "nginx": nginx_balancer,
            "haproxy": haproxy_balancer
        }

        writer.update_configurable(Balancer, "nginx", {})

        args, _ = nginx_balancer.sync_file.call_args
        self.assertEqual(list(args[0]), [app_cluster])

        args, _ = haproxy_balancer.sync_file.call_args
        self.assertEqual(list(args[0]), [app_cluster])

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

        writer = Writer("/etc/configs")

        self.assertEqual(writer.configurables[Discovery], {})

        writer.add_configurable(Discovery, "existing", discovery)

        discovery.connect.assert_called_once_with()

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
            call(cluster2, writer.sync_balancer_files),
            call(cluster3, writer.sync_balancer_files),
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
        dns_discovery.start_watching.assert_called_once_with(
            cluster, writer.sync_balancer_files
        )

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
