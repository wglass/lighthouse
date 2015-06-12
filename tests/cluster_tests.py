try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from lighthouse.cluster import Cluster


class ClusterTests(unittest.TestCase):

    def test_nodes_empty_by_default(self):
        cluster = Cluster()
        self.assertEqual(cluster.nodes, [])

    def test_discovery_required(self):
        self.assertRaises(
            ValueError,
            Cluster.validate_config, {"foo": "bar"}
        )

    @patch("lighthouse.cluster.Coordinator")
    def test_at_least_one_coordinator_section_required(self, Coordinator):
        Coordinator.get_installed_classes.return_value = {
            "acoordinator": Coordinator(),
            "othercoordinator": Coordinator()
        }

        self.assertRaises(
            ValueError,
            Cluster.validate_config, {"discovery": "zookeeper"}
        )

    @patch("lighthouse.cluster.Coordinator")
    def test_applying_config(self, Coordinator):
        Coordinator.get_installed_classes.return_value = {
            "acoordinator": Coordinator(),
            "othercoordinator": Coordinator()
        }

        cluster = Cluster()
        cluster.apply_config({
            "discovery": "zookeeper",
            "acoordinator": {"foo": "bar"}
        })

        self.assertEqual(cluster.discovery, "zookeeper")
        self.assertEqual(cluster.acoordinator, {"foo": "bar"})
        self.assertEqual(cluster.meta_cluster, None)

    @patch("lighthouse.cluster.Coordinator")
    def test_optional_meta_cluster_config(self, Coordinator):
        Coordinator.get_installed_classes.return_value = {
            "acoordinator": Coordinator(),
            "othercoordinator": Coordinator()
        }

        cluster = Cluster()
        cluster.apply_config({
            "discovery": "zookeeper",
            "meta_cluster": "webapi",
            "acoordinator": {"foo": "bar"}
        })

        self.assertEqual(cluster.meta_cluster, "webapi")
