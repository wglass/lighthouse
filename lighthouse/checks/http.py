import logging

from six.moves import http_client as client

from lighthouse import check


logger = logging.getLogger(__name__)


class HTTPCheck(check.Check):
    """
    Simple check for HTTP services.

    Pings a configured uri on the host.  The check passes if the response
    code is in the 2xx range.
    """

    name = "http"

    def __init__(self, *args, **kwargs):
        super(HTTPCheck, self).__init__(*args, **kwargs)

        self.uri = None
        self.use_https = None
        self.method = None

    @classmethod
    def validate_dependencies(cls):
        """
        This check uses stdlib modules so dependencies are always present.
        """
        return True

    @classmethod
    def validate_check_config(cls, config):
        """
        Validates the http check config.  The "uri" key is required.
        """
        if "uri" not in config:
            raise ValueError("Missing uri.")

    def apply_check_config(self, config):
        """
        Takes a validated config dictionary and sets the `uri`, `use_https`
        and `method` attributes based on the config's contents.
        """
        self.uri = config["uri"]
        self.use_https = config.get("https", False)
        self.method = config.get("method", "GET")

    def perform(self):
        """
        Performs a simple HTTP request against the configured url and returns
        true if the response has a 2xx code.

        The url can be configured to use https via the "https" boolean flag
        in the config, as well as a custom HTTP method via the "method" key.

        The default is to not use https and the GET method.
        """
        if self.use_https:
            conn = client.HTTPSConnection(self.host, self.port)
        else:
            conn = client.HTTPConnection(self.host, self.port)

        conn.request(self.method, self.uri)

        response = conn.getresponse()

        conn.close()

        return bool(response.status >= 200 and response.status < 300)
