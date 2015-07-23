try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch, Mock

from lighthouse.check import Check


class BaseCheckTests(unittest.TestCase):

    def test_validate_deps_must_be_implemented(self):
        self.assertRaises(
            NotImplementedError,
            Check.validate_dependencies
        )

    @patch.object(Check, "apply_check_config")
    def test_validate_check_config_must_be_implemented(self, apply_config):
        self.assertRaises(
            NotImplementedError,
            Check.validate_check_config,
            {"foo": "bar"}
        )

    @patch.object(Check, "validate_config", Mock())
    @patch.object(Check, "apply_config", Mock())
    def test_apply_check_config_must_be_implemented(self):
        check = Check()

        self.assertRaises(
            NotImplementedError,
            check.apply_check_config,
            {"host": "serv01", "port": 1234, "rise": 1, "fall": 1}
        )

    @patch.object(Check, "validate_config", Mock())
    @patch.object(Check, "apply_config", Mock())
    def test_perform_must_be_implemented(self):
        check = Check()

        self.assertRaises(
            NotImplementedError,
            check.perform
        )

    @patch.object(Check, "validate_config", Mock())
    @patch.object(Check, "apply_check_config", Mock())
    def test_check_is_not_passing_by_default(self):
        check = Check()

        assert not check.passing

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_check_config")
    def test_validate_config(self, check_validate):
        Check.validate_config(
            {"host": "serv03", "port": 1235, "rise": 2, "fall": 3}
        )

        check_validate.assert_called_once_with(
            {"host": "serv03", "port": 1235, "rise": 2, "fall": 3}
        )

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_check_config")
    def test_validate_config_with_no_host(self, check_validate):
        self.assertRaises(
            ValueError,
            Check.validate_config,
            {"port": 1234, "rise": 1, "fall": 1}
        )

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_check_config")
    def test_validate_config_with_no_port(self, check_validate):
        self.assertRaises(
            ValueError,
            Check.validate_config,
            {"host": "serv03", "rise": 1, "fall": 1}
        )

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_check_config")
    def test_validate_config_with_invalid_port(self, check_validate):
        self.assertRaises(
            ValueError,
            Check.validate_config,
            {"host": "serv03", "port": "foo", "rise": 1, "fall": 1}
        )

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_check_config")
    def test_validate_config_with_no_rise(self, check_validate):
        self.assertRaises(
            ValueError,
            Check.validate_config,
            {"host": "serv03", "port": 1234, "fall": 1}
        )

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_check_config")
    def test_validate_config_with_no_fall(self, check_validate):
        self.assertRaises(
            ValueError,
            Check.validate_config,
            {"host": "serv03", "port": 1234, "rise": 1}
        )

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_config")
    def test_apply_config_coerces_port(self, validate):
        check = Check()
        check.apply_config(
            {"host": "serv01", "port": "1234", "rise": 3, "fall": 1}
        )

        self.assertEqual(check.port, 1234)

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_config")
    def test_results_size_is_greater_of_rise_or_fall(self, validate):
        check = Check()
        check.apply_config(
            {"host": "serv01", "port": 1234, "rise": 3, "fall": 1}
        )

        self.assertEqual(len(check.results), 3)
        assert not any(list(check.results))

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "perform")
    @patch.object(Check, "validate_config")
    def test_last_n_results(self, validate, perform):
        results = [True, False, True, True]

        def get_next_fake_result():
            return results.pop(0)

        perform.side_effect = get_next_fake_result

        check = Check()
        check.apply_config(
            {"host": "serv01", "port": 1234, "rise": 3, "fall": 1}
        )

        check.run()

        self.assertEqual(
            check.last_n_results(2),
            [False, True]
        )

        check.run()

        self.assertEqual(
            check.last_n_results(2),
            [True, False]
        )

        check.run()

        self.assertEqual(
            check.last_n_results(2),
            [False, True]
        )
        self.assertEqual(
            check.last_n_results(3),
            [True, False, True]
        )

        check.run()

        self.assertEqual(
            check.last_n_results(2),
            [True, True]
        )
        self.assertEqual(
            check.last_n_results(3),
            [False, True, True]
        )

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_config", Mock())
    @patch.object(Check, "perform")
    def test_run_sets_passing_flag_if_rise_count_met(self, perform):
        perform.return_value = True

        check = Check()
        check.apply_config(
            {"host": "serv01", "port": 1234, "rise": 2, "fall": 1}
        )

        self.assertEqual(check.passing, False)

        check.run()

        self.assertEqual(check.passing, False)

        check.run()

        self.assertEqual(check.passing, True)

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_config", Mock())
    @patch.object(Check, "perform")
    def test_run_sets_passing_flag_if_fall_count_met(self, perform):
        fake_results = [True, True, False, False]

        def get_next_fake_result():
            return fake_results.pop(0)

        perform.side_effect = get_next_fake_result

        check = Check()
        check.apply_config(
            {"host": "serv01", "port": 1234, "rise": 2, "fall": 2}
        )

        check.run()
        check.run()

        self.assertEqual(check.passing, True)

        check.run()

        self.assertEqual(check.passing, True)

        check.run()

        self.assertEqual(check.passing, False)

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_config", Mock())
    @patch.object(Check, "perform")
    def test_apply_config_with_higher_fall_count(self, perform):
        perform.return_value = True

        config = {"host": "serv01", "port": 1234, "rise": 2, "fall": 2}

        check = Check()
        check.apply_config(config)

        check.run()

        self.assertEqual(
            list(check.results),
            [False, True]
        )

        config["fall"] = 3

        check.apply_config(config)

        self.assertEqual(
            list(check.results),
            [False, False, True]
        )

        check.run()

        self.assertEqual(
            list(check.results),
            [False, True, True]
        )

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_config", Mock())
    @patch.object(Check, "perform")
    def test_apply_config_with_lower_rise_count(self, perform):
        perform.return_value = True

        config = {"host": "serv01", "port": 1234, "rise": 3, "fall": 2}

        check = Check()
        check.apply_config(config)

        check.run()

        self.assertEqual(
            list(check.results),
            [False, False, True]
        )

        config["rise"] = 2

        check.apply_config(config)

        self.assertEqual(
            list(check.results),
            [False, True]
        )

        check.run()

        self.assertEqual(
            list(check.results),
            [True, True]
        )

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_config", Mock())
    @patch.object(Check, "perform")
    def test_apply_config_no_change_in_max_count(self, perform):
        perform.return_value = True

        config = {"host": "serv01", "port": 1234, "rise": 3, "fall": 2}

        check = Check()
        check.apply_config(config)

        check.run()

        self.assertEqual(
            list(check.results),
            [False, False, True]
        )

        config["rise"] = 2
        config["fall"] = 3

        check.apply_config(config)

        self.assertEqual(
            list(check.results),
            [False, False, True]
        )

        check.run()

        self.assertEqual(
            list(check.results),
            [False, True, True]
        )

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_config", Mock())
    @patch.object(Check, "perform")
    def test_error_in_perform_gets_false_result(self, perform):
        perform.side_effect = ValueError

        check = Check()
        check.apply_config(
            {"host": "serv01", "port": 1234, "rise": 2, "fall": 2}
        )

        self.assertEqual(
            list(check.results),
            [False, False]
        )

        check.run()

        self.assertEqual(
            list(check.results),
            [False, False]
        )

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_config", Mock())
    @patch.object(Check, "get_installed_classes")
    def test_from_config_uses_installed_classes(self, get_installed):
        fake_check_class = Mock()
        get_installed.return_value = {
            "fakecheck": fake_check_class
        }

        result = Check.from_config("fakecheck", "serv03", 8001, {"foo": "bar"})

        self.assertEqual(result, fake_check_class.return_value)

        result.apply_config.assert_called_once_with(
            {"host": "serv03", "port": 8001, "foo": "bar"}
        )

    @patch.object(Check, "apply_check_config", Mock())
    @patch.object(Check, "validate_config", Mock())
    @patch.object(Check, "get_installed_classes")
    def test_from_config_with_unknown_check(self, get_installed):
        get_installed.return_value = {
            "fakecheck": Mock()
        }

        self.assertRaises(
            ValueError,
            Check.from_config, "othercheck", "serv01", 8888, {"foo": "bar"}
        )
