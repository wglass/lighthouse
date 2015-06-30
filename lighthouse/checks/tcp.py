import errno
import logging
import socket

from lighthouse import check


SOCKET_BUFFER_SIZE = 4096


logger = logging.getLogger(__name__)


class TCPCheck(check.Check):
    """
    Service health check using TCP request/response messages.

    Sends a certain message to the configured port and passes if the response
    is an expected one.
    """

    name = "tcp"

    def __init__(self, *args, **kwargs):
        super(TCPCheck, self).__init__(*args, **kwargs)

        self.query = None
        self.expected_response = None

    @classmethod
    def validate_dependencies(cls):
        """
        This check uses stdlib modules so dependencies are always present.
        """
        return True

    @classmethod
    def validate_check_config(cls, config):
        """
        Ensures that a query and expected response are configured.
        """
        if "query" not in config:
            raise ValueError("Missing TCP query message.")
        if "response" not in config:
            raise ValueError("Missing expected TCP response message.")

    def apply_check_config(self, config):
        """
        Takes the `query` and `response` fields from a validated config
        dictionary and sets the proper instance attributes.
        """
        self.query = config["query"]
        self.expected_response = config["response"]

    def perform(self):
        """
        Performs a straightforward TCP request and response.

        Sends the TCP `query` to the proper host and port, and loops over the
        socket, gathering response chunks until a full line is acquired.

        If the response line matches the expected value, the check passes. If
        not, the check fails.  The check will also fail if there's an error
        during any step of the send/receive process.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sock.connect((self.host, self.port))

        try:
            sock.sendall(self.query)
        except Exception:
            logger.exception("Error sending TCP query message.")
            sock.close()
            return False

        response = ""

        while True:
            try:
                chunk = sock.recv(SOCKET_BUFFER_SIZE)
                if chunk:
                    response += chunk
            except socket.error as e:
                if e.errno not in [errno.EAGAIN, errno.EINTR]:
                    raise

            if not response:
                break

            if "\n" in response:
                response, extra = response.split("\n", 1)
                break

        logger.debug("response: %s", response)

        if response != self.expected_response:
            logger.warn(
                "Response does not match expected value: %s (expected %s)",
                response, self.expected_response
            )
            sock.close()
            return False

        sock.close()
        return True
