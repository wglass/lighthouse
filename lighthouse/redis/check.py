from __future__ import absolute_import

import logging

from lighthouse.checks.tcp import TCPCheck


logger = logging.getLogger(__name__)


class RedisCheck(TCPCheck):
    """
    Redis service checker.

    Pings a redis server to make sure that it's available.
    """

    name = "redis"

    @classmethod
    def validate_check_config(cls, config):
        """
        The base Check class assures that a host and port are configured so
        this method is a no-op.
        """
        pass

    def apply_check_config(self, config):
        """
        This method doesn't actually use any configuration data, as the query
        and response for redis are already established.
        """
        self.query = "PING"
        self.expected_response = "PONG"
