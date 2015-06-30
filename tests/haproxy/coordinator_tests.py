import sys
import time
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch, Mock, mock_open, call

from lighthouse.haproxy.coordinator import HAProxy


if sys.version_info[0] == 3:
    builtin_module = "builtins"
else:
    builtin_module = "__builtin__"


@patch("lighthouse.haproxy.coordinator.HAProxyControl")
@patch("lighthouse.haproxy.coordinator.HAProxyConfig")
class HAProxyCoordinatorTests(unittest.TestCase):

    def test_config_file_required(self, Config, Control):
        self.assertRaises(
            ValueError,
            HAProxy.validate_config,
            {
                "socket_file": "/var/run/haproxy.sock",
            }
        )

    def test_socket_file_required(self, Config, Control):
        self.assertRaises(
            ValueError,
            HAProxy.validate_config,
            {
                "config_file": "/etc/haproxy/haproxy.conf"
            }
        )

    def test_stats_config_requirements(self, Config, Control):
        self.assertRaises(
            ValueError,
            HAProxy.validate_config,
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "stats": {}
            }
        )

    def test_bare_minimum_config(self, Config, Control):
        value_error_raised = False

        try:
            HAProxy.validate_config({
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
            })
        except ValueError:
            value_error_raised = True

        self.assertEqual(value_error_raised, False)

    def test_proxy_config_requires_port(self, Config, Control):
        self.assertRaises(
            ValueError,
            HAProxy.validate_config,
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "proxies": {
                    "cc_processor": {
                        "upstreams": [
                            {"host": "b2b.partner.com", "port": 88}
                        ]
                    }
                }
            }
        )

    def test_proxy_config_requires_upstreams(self, Config, Control):
        self.assertRaises(
            ValueError,
            HAProxy.validate_config,
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "proxies": {
                    "cc_processor": {
                        "port": 8800,
                    }
                }
            }
        )

    def test_proxy_config_upstream_requires_host(self, Config, Control):
        self.assertRaises(
            ValueError,
            HAProxy.validate_config,
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "proxies": {
                    "cc_processor": {
                        "port": 8800,
                        "upstreams": [
                            {"port": 88}
                        ]
                    }
                }
            }
        )

    def test_proxy_config_upstream_requires_port(self, Config, Control):
        self.assertRaises(
            ValueError,
            HAProxy.validate_config,
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "proxies": {
                    "cc_processor": {
                        "port": 8800,
                        "upstreams": [
                            {"port": 88}
                        ]
                    }
                }
            }
        )

    def test_valid_proxy_config(self, Config, Control):
        value_error_raised = False

        try:
            HAProxy.validate_config({
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "proxies": {
                    "cc_processor": {
                        "port": 8800,
                        "upstreams": [
                            {"host": "b2b.partner.com", "port": 88}
                        ]
                    }
                }
            })
        except ValueError:
            value_error_raised = True
            raise

        self.assertEqual(value_error_raised, False)

    def test_restart_required_defaults_to_true(self, Config, Control):
        coordinator = HAProxy()
        coordinator.apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
            }
        )

        self.assertTrue(coordinator.restart_required)

    @patch("lighthouse.haproxy.coordinator.time")
    def test_restart_delays_if_too_soon_since_last(self,
                                                   mock_time,
                                                   Config, Control):
        mock_time.time.return_value = time.time()
        coordinator = HAProxy()
        coordinator.apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
            }
        )

        coordinator.restart_requred = True
        coordinator.last_restart = mock_time.time.return_value - 1
        coordinator.restart_interval = 4
        coordinator.restart()

        mock_time.sleep.assert_called_once_with(3)

        Control.return_value.restart.assert_called_once_with()
        self.assertEqual(coordinator.restart_required, False)

    @patch.object(HAProxy, "restart")
    @patch.object(HAProxy, "sync_nodes")
    @patch(builtin_module + ".open", mock_open())
    def test_sync_file_syncs_nodes_if_no_restart(self, sync_nodes, restart,
                                                 Config, Control):
        cluster1 = Mock()
        cluster2 = Mock()

        coordinator = HAProxy()
        coordinator.apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
            }
        )

        coordinator.restart_required = False

        coordinator.sync_file([cluster1, cluster2])

        sync_nodes.assert_called_once_with([cluster1, cluster2])
        self.assertEqual(restart.called, False)

    @patch.object(HAProxy, "restart")
    @patch.object(HAProxy, "sync_nodes")
    def test_sync_file_writes_config_to_file(self, sync_nodes, restart,
                                             Config, Control):
        cluster1 = Mock()
        cluster2 = Mock()

        coordinator = HAProxy()
        coordinator.apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
            }
        )

        fake_file = mock_open()

        with patch(builtin_module + ".open", fake_file, create=True):
            coordinator.sync_file([cluster1, cluster2])

        fake_file.return_value.write.assert_called_once_with(
            Config.return_value.generate.return_value
        )
        Config.return_value.generate.assert_called_once_with(
            [cluster1, cluster2],
            version=Control.return_value.get_version.return_value
        )

    @patch.object(HAProxy, "restart")
    @patch.object(HAProxy, "sync_nodes")
    @patch(builtin_module + ".open", mock_open())
    def test_sync_file_restarts_if_required(self, sync_nodes, restart,
                                            Config, Control):
        cluster1 = Mock()
        cluster2 = Mock()

        coordinator = HAProxy()
        coordinator.apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
            }
        )

        coordinator.restart_required = True

        coordinator.sync_file([cluster1, cluster2])

        restart.assert_called_once_with()
        self.assertEqual(sync_nodes.called, False)

    def test_default_and_optional_global_lines(self, Config, Control):
        HAProxy().apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "global": ["user haproxy", "nopoll"],
            }
        )

        config_args, config_kwargs = Config.call_args
        global_stanza, defaults_stanza = config_args

        self.assertEqual(
            global_stanza.lines,
            [
                "user haproxy",
                "nopoll",
                "stats socket /var/run/haproxy.sock mode 600 level admin",
                "stats timeout 2m",
            ]
        )

    def test_optional_defaults_lines(self, Config, Control):
        HAProxy().apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "defaults": ["timeout connect 4000", "invalid line ok"]
            }
        )

        config_args, config_kwargs = Config.call_args
        global_stanza, defaults_stanza = config_args

        self.assertEqual(
            defaults_stanza.lines,
            [
                "timeout connect 4000",
            ]
        )

    def test_config_can_use_custom_bind_address(self, Config, Control):
        HAProxy().apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "bind_address": "127.0.0.1"
            }
        )

        config_args, config_kwargs = Config.call_args
        self.assertEqual(
            config_kwargs["bind_address"], "127.0.0.1"
        )

    def test_optional_meta_cluster_ports_config(self, Config, Control):
        HAProxy().apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "meta_clusters": {
                    "api": {"port": 8000},
                    "compute": {"port": 7777},
                },
            }
        )

        config_args, config_kwargs = Config.call_args
        self.assertEqual(
            config_kwargs["meta_clusters"],
            {
                "api": {"port": 8000},
                "compute": {"port": 7777},
            },
        )

    def test_optional_stats_config(self, Config, Control):
        HAProxy().apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "stats": {"port": 9999}
            }
        )

        config_args, config_kwargs = Config.call_args
        stats_stanza = config_kwargs["stats_stanza"]

        self.assertEqual(stats_stanza.header, "listen stats :9999")
        self.assertEqual(
            stats_stanza.lines,
            [
                "mode http",
                "stats enable",
                "stats uri /"
            ]
        )

    def test_stats_listener_optional_timeouts(self, Config, Control):
        HAProxy().apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "stats": {
                    "port": 9999, "uri": "/haproxy_stats",
                    "timeouts": {
                        "client": 2000,
                        "connect": 4000,
                        "server": 20000,
                    }
                }
            }
        )

        config_args, config_kwargs = Config.call_args
        stats_stanza = config_kwargs["stats_stanza"]

        self.assertEqual(stats_stanza.header, "listen stats :9999")
        self.assertEqual(
            stats_stanza.lines,
            [
                "mode http",
                "stats enable",
                "stats uri /haproxy_stats",
                "timeout client 2000",
                "timeout connect 4000",
                "timeout server 20000",
            ]
        )

    def test_optional_proxy_stanzas(self, Config, Control):
        HAProxy().apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
                "proxies": {
                    "cc_processor": {
                        "port": 8800,
                        "upstreams": [
                            {"host": "b2b.partner.com", "port": 88}
                        ],
                        "options": [
                            "maxconn 400"
                        ]
                    }
                }
            }
        )

        config_args, config_kwargs = Config.call_args
        proxy_stanza = config_kwargs["proxy_stanzas"][0]

        self.assertEqual(proxy_stanza.header, "listen cc_processor")
        self.assertEqual(
            proxy_stanza.lines,
            [
                "bind :8800",
                "maxconn 400",
                "server b2b.partner.com:88 b2b.partner.com:88 "
            ]
        )

    def test_sync_nodes_new_cluster_begets_restart(self, Config, Control):
        node1 = Mock()
        node2 = Mock()
        node3 = Mock()
        node4 = Mock()

        cluster1 = Mock(nodes=[node1, node4])
        cluster1.name = "cluster1"
        cluster2 = Mock(nodes=[node3, node2])
        cluster2.name = "cluster2"

        Control.return_value.get_active_nodes.return_value = {
            "cluster1": [
                {"svname": "app01:8888"},
                {"svname": "app02:8888"},
            ]
        }

        coordinator = HAProxy()
        coordinator.apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
            }
        )
        coordinator.restart_required = False

        coordinator.sync_nodes([cluster1, cluster2])

        self.assertEqual(coordinator.restart_required, True)

    def test_sync_nodes_new_node_begets_restart(self, Config, Control):
        node1 = Mock()
        node4 = Mock()

        cluster1 = Mock(nodes=[node1, node4])
        cluster1.name = "cluster1"

        Control.return_value.get_active_nodes.return_value = {
            "cluster1": [
                {"svname": "app01:8888"},
            ]
        }

        coordinator = HAProxy()
        coordinator.apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
            }
        )
        coordinator.restart_required = False

        coordinator.sync_nodes([cluster1])

        self.assertEqual(coordinator.restart_required, True)

    def test_sync_nodes_clusters_without_nodes(self, Config, Control):
        control = Control.return_value

        node1 = Mock()
        node1.name = "app01:8888"
        node4 = Mock()
        node4.name = "app04:8888"

        cluster1 = Mock(nodes=[node1, node4])
        cluster1.name = "cluster1"
        cluster2 = Mock(nodes=[])
        cluster2.name = "cluster2"

        Control.return_value.get_active_nodes.return_value = {
            "cluster1": [
                {"svname": "app01:8888"},
                {"svname": "app04:8888"},
            ],
            "cluster2": [
                {"svname": "app02:8888"},
                {"svname": "app03:8888"},
            ],
        }

        control.enable_node.return_value = ""
        control.disable_node.return_value = ""

        coordinator = HAProxy()
        coordinator.apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
            }
        )
        coordinator.restart_required = False

        coordinator.sync_nodes([cluster1, cluster2])

        control.disable_node.assert_has_calls([
            call("cluster2", "app02:8888"),
            call("cluster2", "app03:8888"),
        ], any_order=True)
        control.enable_node.assert_has_calls([
            call("cluster1", "app01:8888"),
            call("cluster1", "app04:8888"),
        ], any_order=True)
        self.assertEqual(coordinator.restart_required, False)

    def test_sync_nodes_enable_disable_nodes(self, Config, Control):
        control = Control.return_value

        node1 = Mock()
        node1.name = "app01:8888"
        node2 = Mock()
        node2.name = "app02:8888"
        node3 = Mock()
        node3.name = "app03:8888"
        node4 = Mock()
        node4.name = "app04:8888"

        cluster1 = Mock(nodes=[node1, node3, node4])
        cluster1.name = "cluster1"
        cluster2 = Mock(nodes=[node2])
        cluster2.name = "cluster2"

        Control.return_value.get_active_nodes.return_value = {
            "cluster1": [
                {"svname": "app01:8888"},
                {"svname": "app04:8888"},
            ],
            "cluster2": [
                {"svname": "app02:8888"},
                {"svname": "app03:8888"},
            ],
        }

        control.enable_node.return_value = ""
        control.disable_node.return_value = ""

        coordinator = HAProxy()
        coordinator.apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
            }
        )
        coordinator.restart_required = False

        coordinator.sync_nodes([cluster1, cluster2])

        control.disable_node.assert_has_calls([
            call("cluster2", "app03:8888"),
        ], any_order=True)
        control.enable_node.assert_has_calls([
            call("cluster2", "app02:8888"),
            call("cluster1", "app01:8888"),
            call("cluster1", "app04:8888"),
        ], any_order=True)
        self.assertEqual(coordinator.restart_required, True)

    def test_sync_nodes_error_with_command(self, Config, Control):
        control = Control.return_value

        node1 = Mock()
        node1.name = "app01:8888"
        node4 = Mock()
        node4.name = "app04:8888"

        cluster1 = Mock(nodes=[node1, node4])
        cluster1.name = "cluster1"
        cluster2 = Mock(nodes=[])
        cluster2.name = "cluster2"

        Control.return_value.get_active_nodes.return_value = {
            "cluster1": [
                {"svname": "app01:8888"},
                {"svname": "app04:8888"},
            ],
            "cluster2": [
                {"svname": "app02:8888"},
                {"svname": "app03:8888"},
            ],
        }

        control.enable_node.return_value = ""
        control.disable_node.return_value = "Something went wrong."

        coordinator = HAProxy()
        coordinator.apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
            }
        )
        coordinator.restart_required = False

        coordinator.sync_nodes([cluster1, cluster2])

        control.disable_node.assert_has_calls([
            call("cluster2", "app02:8888"),
        ])
        self.assertEqual(coordinator.restart_required, True)

    def test_sync_nodes_exception_with_command(self, Config, Control):
        control = Control.return_value

        node1 = Mock()
        node1.name = "app01:8888"
        node4 = Mock()
        node4.name = "app04:8888"

        cluster1 = Mock(nodes=[node1, node4])
        cluster1.name = "cluster1"
        cluster2 = Mock(nodes=[])
        cluster2.name = "cluster2"

        Control.return_value.get_active_nodes.return_value = {
            "cluster1": [
                {"svname": "app01:8888"},
                {"svname": "app04:8888"},
            ],
            "cluster2": [
                {"svname": "app02:8888"},
                {"svname": "app03:8888"},
            ],
        }

        control.enable_node.side_effect = Exception("something went wrong")
        control.disable_node.return_value = ""

        coordinator = HAProxy()
        coordinator.apply_config(
            {
                "config_file": "/etc/haproxy/haproxy.conf",
                "socket_file": "/var/run/haproxy.sock",
            }
        )
        coordinator.restart_required = False

        coordinator.sync_nodes([cluster1, cluster2])

        control.disable_node.assert_has_calls([
            call("cluster2", "app02:8888"),
        ], any_order=True)
        control.enable_node.assert_has_calls([
            call("cluster1", "app01:8888"),
            call("cluster1", "app04:8888"),
        ], any_order=True)
        self.assertEqual(coordinator.restart_required, True)
