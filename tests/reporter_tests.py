try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import Mock, patch

from lighthouse.service import Service
from lighthouse.discovery import Discovery
from lighthouse.reporter import Reporter


class ReporterTests(unittest.TestCase):

    @patch("lighthouse.reporter.wait_on_event")
    def test_run_waits_on_shutdown(self, wait_on_event):
        reporter = Reporter("/etc/configs")

        reporter.run()

        wait_on_event.assert_called_once_with(reporter.shutdown)

    @patch("lighthouse.reporter.multiprocessing.pool.ThreadPool")
    def test_wind_down_calls_stop_on_discoveries(self, Pool):
        reporter = Reporter("/etc/configs")

        discovery1 = Mock()
        discovery2 = Mock()

        reporter.configurables[Discovery] = {
            "discovery1": discovery1,
            "discovery2": discovery2
        }

        reporter.wind_down()

        discovery1.stop.assert_called_once_with()
        discovery2.stop.assert_called_once_with()

    @patch("lighthouse.reporter.multiprocessing.pool.ThreadPool")
    def test_wind_down_closes_pool(self, Pool):
        reporter = Reporter("/etc/configs")

        self.assertEqual(reporter.pool, Pool.return_value)

        reporter.wind_down()

        Pool.return_value.join.assert_called_once_with()

    def test_add_discovery_calls_connect(self):
        discovery = Mock()
        discovery.name = "existing"

        reporter = Reporter("/etc/configs")

        self.assertEqual(reporter.configurables[Discovery], {})

        reporter.add_configurable(Discovery, "existing", discovery)

        discovery.connect.assert_called_once_with()

    def test_update_discovery_clears_up_flags(self):
        service = Mock()
        discovery = Mock()

        service.discovery = "disco"
        service.checks = {}

        reporter = Reporter("etc/configs")
        reporter.configurables[Discovery] = {
            "disco": discovery
        }
        reporter.configurables[Service] = {
            "a_service": service
        }

        service.is_up = True

        reporter.update_configurable(Discovery, "disco", {})

        self.assertEqual(service.is_up, None)

    def test_remove_discovery_calls_stop(self):
        discovery = Mock()
        discovery.name = "existing"

        reporter = Reporter("/etc/configs")
        reporter.configurables[Discovery] = {
            "existing": discovery
        }

        reporter.remove_configurable(Discovery, "existing")

        self.assertEqual(reporter.configurables[Discovery], {})

        discovery.stop.assert_called_once_with()

    @patch("lighthouse.reporter.multiprocessing.pool.ThreadPool")
    def test_add_service_starts_check_run_thread(self, Pool):
        service = Mock()
        service.name = "existing"

        thread_pool = Pool.return_value

        reporter = Reporter("/etc/configs")
        reporter.pool = thread_pool

        reporter.add_configurable(Service, "existing", service)

        thread_pool.apply_async.assert_called_once_with(
            reporter.run_checks, [service]
        )

    def test_run_checks_passes_if_shutdown_set(self):
        service = Mock()
        service.name = "a_service"

        reporter = Reporter("/etc/configs")

        reporter.shutdown.set()

        reporter.run_checks(service)

    def test_run_checks_passes_if_service_not_in_services(self):
        service = Mock()
        service.name = "other_service"

        reporter = Reporter("/etc/configs")
        reporter.configurables[Service] = {
            "a_service": Mock()
        }

        reporter.run_checks(service)

    @patch("lighthouse.reporter.wait_on_event")
    def test_run_checks_loops_with_check_interval(self, wait_on_event):
        service = Mock()

        reporter = Reporter("etc/configs")

        def set_shutdown(*args, **wargs):
            reporter.shutdown.set()

        wait_on_event.side_effect = set_shutdown

        reporter.configurables[Service] = {
            "a_service": service
        }

        reporter.run_checks(service)

        wait_on_event.assert_called_once_with(
            reporter.shutdown, timeout=service.check_interval
        )

    @patch("lighthouse.reporter.wait_on_event")
    def test_run_checks_runs_each_service_check(self, wait_on_event):
        check1 = Mock()
        check2 = Mock()

        service = Mock()
        service.name = "a_service"
        service.discovery = "foobar"
        service.checks = {
            "check1": check1,
            "check2": check2
        }

        reporter = Reporter("etc/configs")
        reporter.configurables[Discovery] = {
            "foobar": Mock()
        }
        reporter.configurables[Service] = {
            "a_service": service
        }

        def set_shutdown(*args, **kwargs):
            reporter.shutdown.set()

        wait_on_event.side_effect = set_shutdown

        reporter.run_checks(service)

        check1.run.assert_called_once_with()
        check2.run.assert_called_once_with()

    @patch("lighthouse.reporter.wait_on_event")
    def test_run_checks_service_uses_unknown_discovery(self, wait_on_event):
        check1 = Mock()
        check2 = Mock()

        service = Mock()
        service.name = "a_service"
        service.discovery = "fake_discovery"
        service.checks = {
            "check1": check1,
            "check2": check2
        }

        reporter = Reporter("etc/configs")
        reporter.configurables[Discovery] = {
            "foobar": Mock()
        }

        def set_shutdown(*args, **kwargs):
            reporter.shutdown.set()

        wait_on_event.side_effect = set_shutdown

        reporter.configurables[Service] = {
            "a_service": service
        }

        reporter.run_checks(service)

        assert check1.run.called is False
        assert check2.run.called is False

    @patch("lighthouse.reporter.wait_on_event")
    def test_run_checks_up_service_fails(self, wait_on_event):
        check = Mock()
        check.passing = False

        discovery = Mock()

        service = Mock()
        service.is_up = True
        service.discovery = "disco"
        service.checks = {
            "check1": check,
        }

        reporter = Reporter("etc/configs")
        reporter.configurables[Discovery] = {
            "disco": discovery
        }
        reporter.configurables[Service] = {
            service.name: service
        }

        def set_shutdown(*args, **kwargs):
            reporter.shutdown.set()

        wait_on_event.side_effect = set_shutdown

        reporter.run_checks(service)

        discovery.report_down.assert_called_once_with(service)

    @patch("lighthouse.reporter.wait_on_event")
    def test_run_checks_down_service_passes(self, wait_on_event):
        check = Mock()
        check.passing = True

        discovery = Mock()

        service = Mock()
        service.name = "service"
        service.is_up = False
        service.discovery = "disco"
        service.checks = {
            "check1": check,
        }

        reporter = Reporter("etc/configs")
        reporter.configurables[Discovery] = {
            "disco": discovery
        }

        def set_shutdown(*args, **kwargs):
            reporter.shutdown.set()

        wait_on_event.side_effect = set_shutdown

        reporter.configurables[Service] = {
            "service": service
        }

        reporter.run_checks(service)

        discovery.report_up.assert_called_once_with(service)

    @patch("lighthouse.reporter.wait_on_event")
    def test_run_checks_with_no_checks_defined(self, wait_on_event):
        check = Mock()
        check.passing = True

        discovery = Mock()

        service = Mock()
        service.name = "service"
        service.is_up = False
        service.discovery = "disco"
        service.checks = {}

        reporter = Reporter("etc/configs")
        reporter.configurables[Discovery] = {
            "disco": discovery
        }

        def set_shutdown(*args, **kwargs):
            reporter.shutdown.set()

        wait_on_event.side_effect = set_shutdown

        reporter.configurables[Service] = {
            "service": service
        }

        reporter.run_checks(service)

        wait_on_event.assert_called_once_with(
            reporter.shutdown, timeout=service.check_interval
        )
