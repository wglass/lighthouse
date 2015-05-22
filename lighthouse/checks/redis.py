from __future__ import absolute_import

import logging

try:
    from redis import Redis
    redis_available = True  # pragma: no cover
except ImportError:
    redis_available = False

from lighthouse import check


logger = logging.getLogger(__name__)


class RedisCheck(check.Check):
    """
    Redis service checker.

    Pings a redis server to make sure that it's available.
    """

    name = "redis"

    @classmethod
    def validate_dependencies(cls):
        """
        Validates that the redis python library is installed.
        """
        if not redis_available:
            logger.error("Redis check requires the 'redis' library.")
            return False

        return True

    @classmethod
    def validate_check_config(cls, config):
        """
        The base Check class assures that a host and port are configured so
        this method is a no-op.
        """
        pass

    def apply_check_config(self, config):
        """
        This method is a no-op as there is no redis-specific configuration
        available.
        """
        pass

    def perform(self):
        """
        Calls the ping() method on a Redis client connected to the target host
        and returns the result.
        """
        return Redis(host=self.host, port=self.port).ping()
