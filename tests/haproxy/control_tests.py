import errno
import socket
import subprocess
import sys
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch, Mock, mock_open

from lighthouse.haproxy.control import (
    HAProxyControl,
    UnknownCommandError, PermissionError, UnknownServerError
)


if sys.version_info[0] == 3:
    builtin_module = "builtins"
else:
    builtin_module = "__builtin__"


class HAProxyControlTests(unittest.TestCase):

    def setUp(self):
        self.stub_commands = {}

        self.command_patcher = patch.object(HAProxyControl, "send_command")

        mock_send_command = self.command_patcher.start()

        def stop_command_patcher():
            try:
                self.command_patcher.stop()
            except RuntimeError:
                pass

        self.addCleanup(stop_command_patcher)

        def get_stub_response(command):
            if command not in self.stub_commands:
                raise AssertionError("Got un-stubbed command '%s'" % command)

            return self.stub_commands[command]

        mock_send_command.side_effect = get_stub_response

    @patch("lighthouse.haproxy.control.Peer")
    def test_gets_current_peer(self, Peer):
        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertEqual(ctl.peer, Peer.current.return_value)

    @patch("lighthouse.haproxy.control.subprocess")
    def test_get_version(self, mock_subprocess):
        mock_subprocess.check_output.return_value = "\n".join((
            "HA-Proxy version 1.5.9 2014/11/25",
            "Copyright 2000-2014 Willy Tarreau <w@1wt.eu>"
        ))

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertEqual(ctl.get_version(), (1, 5, 9))

    @patch("lighthouse.haproxy.control.subprocess")
    def test_get_version__error(self, mock_subprocess):
        mock_subprocess.CalledProcessError = subprocess.CalledProcessError

        error = subprocess.CalledProcessError(-1, "haproxy")
        mock_subprocess.check_output.side_effect = error

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertEqual(ctl.get_version(), None)

    @patch("lighthouse.haproxy.control.subprocess")
    def test_get_version__weird_output(self, mock_subprocess):
        mock_subprocess.check_output.return_value = "\n".join((
            "HA-Proxy version wefaewlfkjalwekja;kj",
        ))

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertEqual(ctl.get_version(), None)

    def test_enable_node(self):
        self.stub_commands = {
            "enable server rediscache/redis01": "OK"
        }

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        result = ctl.enable_node("rediscache", "redis01")

        self.assertEqual(result, "OK")

    def test_disable_node(self):
        self.stub_commands = {
            "disable server rediscache/redis02": "OK"
        }

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        result = ctl.disable_node("rediscache", "redis02")

        self.assertEqual(result, "OK")

    def test_get_active_nodes(self):
        self.stub_commands = {
            "show stat -1 4 -1":
            """# pxname,svname,qcur,qmax,scur,smax,slim,stot,bin,bout,dreq
rediscache,redis01,,,0,0,1000,0,0,500,0
rediscache,redis02,0,0,0,0,1000,0,0,0,1000
web,app03,0,0,0,0,1000,0,0,0,0"""
        }

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertEqual(
            ctl.get_active_nodes(),
            {
                "rediscache": [
                    {
                        'bin': '0', 'smax': '0', 'scur': '0', 'stot': '0',
                        'slim': '1000', 'qmax': '', 'dreq': '0', 'qcur': '',
                        'bout': '500', 'svname': 'redis01'
                    },
                    {
                        'bin': '0', 'smax': '0', 'scur': '0', 'stot': '0',
                        'slim': '1000', 'qmax': '0', 'dreq': '1000', 'qcur':
                        '0', 'bout': '0', 'svname': 'redis02'
                    },
                ],
                "web": [
                    {
                        "svname": "app03",
                        'bin': '0', 'smax': '0', 'scur': '0', 'stot': '0',
                        'slim': '1000', 'qmax': '0', 'dreq': '0', 'qcur': '0',
                        'bout': '0'
                    },
                ]
            }
        )

    def test_get_active_nodes__no_response(self):
        self.stub_commands = {
            "show stat -1 4 -1": ""
        }

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertEqual(
            ctl.get_active_nodes(),
            []
        )

    def test_get_info(self):
        self.stub_commands = {
            "show info": """Name: HAProxy
Version: 1.4-dev2-49
Release_date: 2009/09/23
Nbproc: 1
Process_num: 1
Pid: 12334"""
        }

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertEqual(
            ctl.get_info(),
            {
                "name": "HAProxy",
                "nbproc": "1",
                "pid": "12334",
                "process_num": "1",
                "version": "1.4-dev2-49",
                "release_date": "2009/09/23"
            }
        )

    def test_info__no_response(self):
        self.stub_commands = {
            "show info": ""
        }

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertEqual(ctl.get_info(), {})

    @patch.object(HAProxyControl, "get_version")
    @patch("lighthouse.haproxy.control.Peer")
    @patch("lighthouse.haproxy.control.os")
    @patch("lighthouse.haproxy.control.subprocess")
    @patch(builtin_module + ".open", mock_open(read_data="12355"))
    def test_restart_with_peer(
            self, mock_subprocess, mock_os, Peer, get_version
    ):
        get_version.return_value = (1, 5, 11)
        mock_os.path.exists.return_value = True

        peer = Mock(host="app08", port=8888)
        peer.name = "app08"
        Peer.current.return_value = peer

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        ctl.restart()

        mock_subprocess.check_output.assert_called_once_with([
            "haproxy", "-f", "/etc/haproxy.cfg", "-p", "/var/run/haproxy.pid",
            "-L", "app08", "-sf", "12355"
        ])

    @patch.object(HAProxyControl, "get_version")
    @patch("lighthouse.haproxy.control.Peer")
    @patch("lighthouse.haproxy.control.os")
    @patch("lighthouse.haproxy.control.subprocess")
    @patch(builtin_module + ".open", mock_open(read_data="12355"))
    def test_restart_without_peer(
            self, mock_subprocess, mock_os, Peer, get_version
    ):
        get_version.return_value = (1, 4, 9)
        mock_os.path.exists.return_value = True

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        ctl.restart()

        mock_subprocess.check_output.assert_called_once_with([
            "haproxy", "-f", "/etc/haproxy.cfg",  "-p", "/var/run/haproxy.pid",
            "-sf", "12355"
        ])

    @patch.object(HAProxyControl, "get_version")
    @patch("lighthouse.haproxy.control.Peer")
    @patch("lighthouse.haproxy.control.os")
    @patch("lighthouse.haproxy.control.subprocess")
    def test_restart_without_peer_or_pid_file(
            self, mock_subprocess, mock_os, Peer, get_version
    ):
        get_version.return_value = (1, 4, 9)
        mock_os.path.exists.return_value = False

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        ctl.restart()

        mock_subprocess.check_output.assert_called_once_with([
            "haproxy", "-f", "/etc/haproxy.cfg",  "-p", "/var/run/haproxy.pid",
        ])

    @patch("lighthouse.haproxy.control.Peer")
    @patch("lighthouse.haproxy.control.os")
    @patch("lighthouse.haproxy.control.subprocess")
    @patch(builtin_module + ".open", mock_open(read_data="12355"))
    def test_restart__process_error(self, mock_subprocess, mock_os, Peer):
        mock_subprocess.CalledProcessError = subprocess.CalledProcessError
        mock_os.path.exists.return_value = True

        peer = Mock(host="app08", port=8888)
        peer.name = "app08:8888"
        Peer.current.return_value = peer

        error = subprocess.CalledProcessError(-1, "haproxy")

        mock_subprocess.check_output.side_effect = error
        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        ctl.restart()

        mock_subprocess.check_output.assert_called_with([
            "haproxy", "-f", "/etc/haproxy.cfg", "-p", "/var/run/haproxy.pid",
            "-sf", "12355"
        ])

    @patch.object(HAProxyControl, "get_info")
    @patch.object(HAProxyControl, "get_version", Mock(return_value=(1, 4, 12)))
    @patch("lighthouse.haproxy.control.subprocess")
    def test_restart__get_info_error(self, mock_subprocess, mock_get_info):
        mock_get_info.side_effect = Exception("oh no!")
        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        ctl.restart()

        mock_subprocess.check_output.assert_called_with([
            "haproxy", "-f", "/etc/haproxy.cfg", "-p", "/var/run/haproxy.pid"
        ])

    @patch("lighthouse.haproxy.control.socket")
    def test_send_command_uses_sendall_and_closes_socket(self, mock_socket):
        self.command_patcher.stop()

        mock_sock = mock_socket.socket.return_value

        mock_sock.recv.return_value = ""

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        ctl.send_command("show foobar")

        mock_socket.socket.assert_called_once_with(
            mock_socket.AF_UNIX, mock_socket.SOCK_STREAM
        )
        mock_sock.connect.assert_called_once_with("/var/run/haproxy.sock")
        mock_sock.sendall.assert_called_once_with(b"show foobar\n")
        mock_sock.close.assert_called_once_with()

    @patch("lighthouse.haproxy.control.socket")
    def test_send_command_error_connection_refused(self, mock_socket):
        mock_socket.error = socket.error
        self.command_patcher.stop()

        mock_sock = mock_socket.socket.return_value

        mock_sock.connect.side_effect = socket.error(
            errno.ECONNREFUSED, ""
        )

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        result = ctl.send_command("show info")

        self.assertEqual(result, None)

    @patch("lighthouse.haproxy.control.socket")
    def test_send_command_error_other_connection_error(self, mock_socket):
        mock_socket.error = socket.error
        self.command_patcher.stop()

        mock_sock = mock_socket.socket.return_value

        mock_sock.connect.side_effect = socket.error(
            errno.ENOMEM, ""
        )

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertRaises(
            socket.error,
            ctl.send_command, "show info"
        )

    @patch("lighthouse.haproxy.control.socket")
    def test_send_command_handles_flaky_socket(self, mock_socket):
        mock_socket.error = socket.error

        self.command_patcher.stop()

        mock_sock = mock_socket.socket.return_value

        response_chunks = [
            b"EVERYTHING",
            socket.error(errno.EAGAIN, ""),
            b" A-",
            socket.error(errno.EINTR, ""),
            socket.error(errno.EINTR, ""),
            b"OK\n",
            b"\n"
        ]

        def get_next_chunk(bufsize):
            try:
                chunk = response_chunks.pop(0)
            except IndexError:
                return ""

            if isinstance(chunk, Exception):
                raise chunk
            return chunk

        mock_sock.recv.side_effect = get_next_chunk

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        result = ctl.send_command("show foobar")

        self.assertEqual(result, "EVERYTHING A-OK")

    @patch("lighthouse.haproxy.control.socket")
    def test_send_command_really_flaky_socket(self, mock_socket):
        mock_socket.error = socket.error

        self.command_patcher.stop()

        mock_sock = mock_socket.socket.return_value

        response_chunks = [
            b"EVERYTHING",
            socket.error(errno.ECONNREFUSED, ""),
        ]

        def get_next_chunk(bufsize):
            try:
                chunk = response_chunks.pop(0)
            except IndexError:
                return ""

            if isinstance(chunk, Exception):
                raise chunk
            return chunk

        mock_sock.recv.side_effect = get_next_chunk

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertRaises(
            socket.error,
            ctl.send_command, "show foobar"
        )

    @patch("lighthouse.haproxy.control.socket")
    def test_unknown_command_response(self, mock_socket):
        self.command_patcher.stop()

        mock_sock = mock_socket.socket.return_value

        chunks = [b"Unknown command.", b"\n", ""]

        def get_next_chunk(bufsize):
            return chunks.pop(0)

        mock_sock.recv.side_effect = get_next_chunk

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertRaises(
            UnknownCommandError,
            ctl.send_command, "show foobar"
        )

    @patch("lighthouse.haproxy.control.socket")
    def test_permission_denied_response(self, mock_socket):
        self.command_patcher.stop()

        mock_sock = mock_socket.socket.return_value

        chunks = [b"Permission denied.\n", ""]

        def get_next_chunk(bufsize):
            return chunks.pop(0)

        mock_sock.recv.side_effect = get_next_chunk

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertRaises(
            PermissionError,
            ctl.send_command, "show foobar"
        )

    @patch("lighthouse.haproxy.control.socket")
    def test_no_such_backend_response(self, mock_socket):
        self.command_patcher.stop()

        mock_sock = mock_socket.socket.return_value

        chunks = [b"No such backend.\n", None]

        def get_next_chunk(bufsize):
            return chunks.pop(0)

        mock_sock.recv.side_effect = get_next_chunk

        ctl = HAProxyControl(
            "/etc/haproxy.cfg", "/var/run/haproxy.sock", "/var/run/haproxy.pid"
        )

        self.assertRaises(
            UnknownServerError,
            ctl.send_command, "disable server foobar/bazz"
        )
