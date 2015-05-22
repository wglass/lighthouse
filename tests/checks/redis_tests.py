try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from lighthouse.checks.redis import RedisCheck


@patch("lighthouse.checks.redis.Redis", create=True)
class RedisCheckTests(unittest.TestCase):

    @patch("lighthouse.checks.redis.redis_available", True)
    def test_dependency_on_redis(self, StrictRedis):
        self.assertEqual(RedisCheck.validate_dependencies(), True)

    @patch("lighthouse.checks.redis.redis_available", False)
    def test_dependency_when_redis_not_available(self, StrictRedis):
        self.assertEqual(RedisCheck.validate_dependencies(), False)

    def test_validate_check_config(self, StrictRedis):
        self.assertEqual(
            RedisCheck.validate_check_config({"foo": "bar"}),
            None
        )

    def test_perform_just_pings_redis(self, StrictRedis):
        check = RedisCheck()
        check.apply_config(
            {"host": "localhost", "port": 6666, "rise": 1, "fall": 1}
        )

        result = check.perform()

        StrictRedis.assert_called_once_with(host="localhost", port=6666)

        self.assertEqual(
            result,
            StrictRedis.return_value.ping.return_value
        )
