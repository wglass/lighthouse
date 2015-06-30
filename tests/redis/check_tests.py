try:
    import unittest2 as unittest
except ImportError:
    import unittest

from lighthouse.redis.check import RedisCheck


class RedisCheckTests(unittest.TestCase):

    def test_query_and_response_values(self):
        check = RedisCheck()
        check.apply_config({
            "host": "127.0.0.1", "port": 1234,
            "rise": 1, "fall": 1
        })

        self.assertEqual(check.query, "PING")
        self.assertEqual(check.expected_response, "PONG")
