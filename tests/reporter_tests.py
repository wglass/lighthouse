try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import Mock, patch

from lighthouse.service import Service
from lighthouse.discovery import Discovery
from lighthouse.reporter import Reporter


class ReporterTests(unittest.TestCase):

    def setUp(self):
        super(ReporterTests, self).setUp()

        futures_patcher = patch("lighthouse.reporter.futures")
        mock_futures = futures_patcher.start()

        executor = mock_futures.ThreadPoolExecutor.return_value

        state = {}

        def fire_immediately(cb):
            cb(state["future"])

        def create_future(fn, *args, **kwargs):
            f = Mock()
            f.add_done_callback.side_effect = fire_immediately
            f.result.return_value = fn(*args, **kwargs)

            state["future"] = f

            return state["future"]

        executor.submit.side_effect = create_future

        self.addCleanup(futures_patcher.stop)

    @patch("lighthouse.reporter.wait_on_event")
    def test_run_waits_on_shutdown(self, wait_on_event):
        reporter = Reporter("/etc/configs")

        reporter.run()

        wait_on_event.assert_called_once_with(reporter.shutdown)

    @patch("lighthouse.reporter.futures.ThreadPoolExecutor")
    def test_wind_down_calls_stop_on_discoveries(self, Executor):
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

    @patch("lighthouse.reporter.futures.ThreadPoolExecutor")
    def test_wind_down_closes_pool(self, Executor):
        reporter = Reporter("/etc/configs")

        self.assertEqual(reporter.pool, Executor.return_value)

        reporter.wind_down()

        Executor.return_value.shutdown.assert_called_once_with()

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

    @patch("lighthouse.reporter.futures.ThreadPoolExecutor")
    @patch("lighthouse.reporter.threading.Thread")
    def test_add_service_starts_check_run_thread(self, Thread, Executor):
        service = Mock()
        service.name = "existing"

        reporter = Reporter("/etc/configs")

        reporter.add_configurable(Service, "existing", service)

        self.assertEqual(
            reporter.check_threads["existing"], Thread.return_value
        )
        Thread.assert_called_once_with(
            target=reporter.check_loop, args=(service,)
        )
        Thread.return_value.start.assert_called_once_with()

    def test_check_loop_passes_if_shutdown_set(self):
        service = Mock()
        service.name = "a_service"
        service.run_checks.return_value = (set(), set())

        reporter = Reporter("/etc/configs")

        reporter.shutdown.set()

        reporter.check_loop(service)

    def test_check_loop_passes_if_service_not_in_services(self):
        service = Mock()
        service.name = "other_service"
        service.run_checks.return_value = (set(), set())

        reporter = Reporter("/etc/configs")
        reporter.configurables[Service] = {
            "a_service": Mock()
        }

        reporter.check_loop(service)

    @patch("lighthouse.reporter.wait_on_event")
    def test_check_loop_loops_with_check_interval(self, wait_on_event):
        service = Mock()
        service.run_checks.return_value = (set(), set())

        reporter = Reporter("etc/configs")

        def set_shutdown(*args, **wargs):
            reporter.shutdown.set()

        wait_on_event.side_effect = set_shutdown

        reporter.configurables[Service] = {
            "a_service": service
        }

        reporter.check_loop(service)

        wait_on_event.assert_called_once_with(
            reporter.shutdown, timeout=service.check_interval
        )

    @patch("lighthouse.reporter.wait_on_event")
    def test_run_checks_service_uses_unknown_discovery(self, wait_on_event):
        service = Mock()
        service.name = "a_service"
        service.discovery = "fake_discovery"
        service.run_checks.return_value = (set(), set())

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

        reporter.check_loop(service)

        assert service.run_check.called is False

    @patch("lighthouse.reporter.wait_on_event")
    def test_check_loop_up_service_fails(self, wait_on_event):
        discovery = Mock()

        service = Mock()
        service.name = "app"
        service.is_up = True
        service.discovery = "disco"
        service.run_checks.return_value = (set(), set([8888]))

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

        reporter.check_loop(service)

        discovery.report_down.assert_called_once_with(service, 8888)

    @patch("lighthouse.reporter.wait_on_event")
    def test_check_loop_down_service_passes(self, wait_on_event):
        discovery = Mock()

        service = Mock()
        service.name = "service"
        service.is_up = False
        service.discovery = "disco"
        service.run_checks.return_value = (set([8888]), set())

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

        reporter.check_loop(service)

        discovery.report_up.assert_called_once_with(service, 8888)

    @patch("lighthouse.reporter.wait_on_event")
    def test_check_loop_with_no_checks_defined(self, wait_on_event):
        discovery = Mock()

        service = Mock()
        service.name = "service"
        service.is_up = False
        service.discovery = "disco"
        service.checks = {}
        service.run_checks.return_value = (set(), set())

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

        reporter.check_loop(service)

        wait_on_event.assert_called_once_with(
            reporter.shutdown, timeout=service.check_interval
        )
