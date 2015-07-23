try:
    import unittest2 as unittest
except ImportError:
    import unittest
import errno
import socket

from mock import patch

from lighthouse.checks.tcp import TCPCheck


@patch("lighthouse.checks.tcp.socket")
class TCPCheckTests(unittest.TestCase):

    def test_no_dependencies(self, mock_socket):
        self.assertEqual(TCPCheck.validate_dependencies(), True)

    def test_valid_config(self, mock_socket):
        TCPCheck.validate_check_config({"query": "ruok", "response": "imok"})

    def test_query_required_if_response_present(self, mock_socket):
        self.assertRaises(
            ValueError,
            TCPCheck.validate_check_config,
            {"response": "imok"}
        )

    def test_response_required_if_query_present(self, mock_socket):
        self.assertRaises(
            ValueError,
            TCPCheck.validate_check_config,
            {"query": "imok"}
        )

    def test_no_response_query(self, mock_socket):
        TCPCheck.validate_check_config({})

    def test_apply_config(self, mock_socket):
        check = TCPCheck()

        self.assertEqual(check.query, None)
        self.assertEqual(check.expected_response, None)

        check.apply_check_config({"query": "ruok", "response": "imok"})

        self.assertEqual(check.query, "ruok")
        self.assertEqual(check.expected_response, "imok")

    def test_error_during_send(self, mock_socket):
        sock = mock_socket.socket.return_value
        sock.sendall.side_effect = Exception("oh no!")

        check = TCPCheck()
        check.apply_config({
            "host": "127.0.0.1", "port": 1234,
            "query": "ruok", "response": "imok",
            "rise": 1, "fall": 1
        })

        self.assertEqual(check.perform(), False)

        sock.close.assert_called_once_with()

    def test_error_during_connect(self, mock_socket):
        sock = mock_socket.socket.return_value
        sock.connect.side_effect = Exception("oh no!")

        check = TCPCheck()
        check.apply_config({
            "host": "127.0.0.1", "port": 1234,
            "query": "ruok", "response": "imok",
            "rise": 1, "fall": 1
        })

        self.assertRaises(
            Exception,
            check.perform
        )

    def test_error_during_recv(self, mock_socket):
        sock = mock_socket.socket.return_value
        sock.recv.side_effect = Exception("oh no!")

        check = TCPCheck()
        check.apply_config({
            "host": "127.0.0.1", "port": 1234,
            "query": "ruok", "response": "imok",
            "rise": 1, "fall": 1
        })

        self.assertRaises(
            Exception,
            check.perform
        )

    def test_mismatch_response(self, mock_socket):
        sock = mock_socket.socket.return_value
        sock.recv.return_value = "notok\n"

        check = TCPCheck()
        check.apply_config({
            "host": "127.0.0.1", "port": 1234,
            "query": "ruok", "response": "imok",
            "rise": 1, "fall": 1
        })

        self.assertEqual(check.perform(), False)

        sock.sendall.assert_called_once_with("ruok")

        sock.close.assert_called_once_with()

    def test_matching_response(self, mock_socket):
        sock = mock_socket.socket.return_value
        sock.recv.return_value = "imok\n"

        check = TCPCheck()
        check.apply_config({
            "host": "127.0.0.1", "port": 1234,
            "query": "ruok", "response": "imok",
            "rise": 1, "fall": 1
        })

        self.assertEqual(check.perform(), True)

        sock.sendall.assert_called_once_with("ruok")

        sock.close.assert_called_once_with()

    def test_chunked_response(self, mock_socket):
        sock = mock_socket.socket.return_value

        chunks = ["im", "ok", "\n"]

        def get_next_chunk(*args):
            chunk = chunks.pop(0)
            if isinstance(chunk, Exception):
                raise chunk
            else:
                return chunk

        sock.recv.side_effect = get_next_chunk

        check = TCPCheck()
        check.apply_config({
            "host": "127.0.0.1", "port": 1234,
            "query": "ruok", "response": "imok",
            "rise": 1, "fall": 1
        })

        self.assertEqual(check.perform(), True)

        sock.close.assert_called_once_with()

    def test_blank_response(self, mock_socket):
        sock = mock_socket.socket.return_value
        sock.recv.return_value = None

        check = TCPCheck()
        check.apply_config({
            "host": "127.0.0.1", "port": 1234,
            "query": "ruok", "response": "imok",
            "rise": 1, "fall": 1
        })

        self.assertEqual(check.perform(), False)

        sock.sendall.assert_called_once_with("ruok")

        sock.close.assert_called_once_with()

    def test_recv_interrupted(self, mock_socket):
        mock_socket.error = socket.error
        sock = mock_socket.socket.return_value

        again = socket.error(errno.EAGAIN, "try again")
        interrupt = socket.error(errno.EINTR, "interrupted!")

        chunks = ["im", interrupt, "ok", again, "\n"]

        def get_next_chunk(*args):
            chunk = chunks.pop(0)
            if isinstance(chunk, Exception):
                raise chunk
            else:
                return chunk

        sock.recv.side_effect = get_next_chunk

        check = TCPCheck()
        check.apply_config({
            "host": "127.0.0.1", "port": 1234,
            "query": "ruok", "response": "imok",
            "rise": 1, "fall": 1
        })

        self.assertEqual(check.perform(), True)

        sock.close.assert_called_once_with()

    def test_recv_socket_error(self, mock_socket):
        mock_socket.error = socket.error
        sock = mock_socket.socket.return_value

        interrupt = socket.error(errno.EINTR, "interrupted!")
        network_down = socket.error(errno.ENETDOWN, "network's down :/")

        chunks = ["im", interrupt, network_down, "ok", "\n"]

        def get_next_chunk(*args):
            chunk = chunks.pop(0)
            if isinstance(chunk, Exception):
                raise chunk
            else:
                return chunk

        sock.recv.side_effect = get_next_chunk

        check = TCPCheck()
        check.apply_config({
            "host": "127.0.0.1", "port": 1234,
            "query": "ruok", "response": "imok",
            "rise": 1, "fall": 1
        })

        self.assertRaises(
            socket.error,
            check.perform
        )

    def test_connection_success_with_no_query(self, mock_socket):
        sock = mock_socket.socket.return_value
        sock.recv.return_value = "notok\n"

        check = TCPCheck()
        check.apply_config({
            "host": "127.0.0.1", "port": 1234,
            "rise": 1, "fall": 1
        })

        self.assertEqual(check.perform(), True)

        assert sock.sendall.called is False
        assert sock.recv.called is False

        sock.close.assert_called_once_with()
