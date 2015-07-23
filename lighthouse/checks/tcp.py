import logging
import socket

from lighthouse import check, sockutils


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
        if "query" not in config and "response" in config:
            raise ValueError("Missing TCP query message.")
        if "response" not in config and "query" in config:
            raise ValueError("Missing expected TCP response message.")

    def apply_check_config(self, config):
        """
        Takes the `query` and `response` fields from a validated config
        dictionary and sets the proper instance attributes.
        """
        self.query = config.get("query")
        self.expected_response = config.get("response")

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

        # if no query/response is defined, a successful connection is a pass
        if not self.query:
            sock.close()
            return True

        try:
            sock.sendall(self.query)
        except Exception:
            logger.exception("Error sending TCP query message.")
            sock.close()
            return False

        response, extra = sockutils.get_response(sock)

        logger.debug("response: %s (extra: %s)", response, extra)

        if response != self.expected_response:
            logger.warn(
                "Response does not match expected value: %s (expected %s)",
                response, self.expected_response
            )
            sock.close()
            return False

        sock.close()
        return True
