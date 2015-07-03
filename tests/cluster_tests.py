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

    @patch("lighthouse.cluster.Balancer")
    def test_at_least_one_balancer_section_required(self, Balancer):
        Balancer.get_installed_classes.return_value = {
            "abalancer": Balancer(),
            "otherbalancer": Balancer()
        }

        self.assertRaises(
            ValueError,
            Cluster.validate_config, {"discovery": "zookeeper"}
        )

    @patch("lighthouse.cluster.Balancer")
    def test_applying_config(self, Balancer):
        Balancer.get_installed_classes.return_value = {
            "abalancer": Balancer(),
            "otherbalancer": Balancer()
        }

        cluster = Cluster()
        cluster.apply_config({
            "discovery": "zookeeper",
            "abalancer": {"foo": "bar"}
        })

        self.assertEqual(cluster.discovery, "zookeeper")
        self.assertEqual(cluster.abalancer, {"foo": "bar"})
        self.assertEqual(cluster.meta_cluster, None)

    @patch("lighthouse.cluster.Balancer")
    def test_optional_meta_cluster_config(self, Balancer):
        Balancer.get_installed_classes.return_value = {
            "abalancer": Balancer(),
            "otherbalancer": Balancer()
        }

        cluster = Cluster()
        cluster.apply_config({
            "discovery": "zookeeper",
            "meta_cluster": "webapi",
            "abalancer": {"foo": "bar"}
        })

        self.assertEqual(cluster.meta_cluster, "webapi")
