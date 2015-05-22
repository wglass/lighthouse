import logging
import multiprocessing.pool
import threading

from .configs.watcher import ConfigWatcher
from .discovery import Discovery
from .service import Service
from .events import wait_on_event


logger = logging.getLogger(__name__)


class Reporter(ConfigWatcher):
    """
    The service node reporting class.

    This config watcher manages Discovery and Service configurables.  For
    every service configured, a thread is created that periodically runs the
    service's checks and reports the current node as up or down to the
    service's chosen discovery method.
    """

    watched_configurables = (Discovery, Service)

    def __init__(self, *args, **kwargs):
        super(Reporter, self).__init__(*args, **kwargs)

        self.pool = multiprocessing.pool.ThreadPool()

    def run(self):
        """
        Since each check the reporter runs is a separate thread the main
        thread does nothing and waits on the `shutdown` thread event.
        """
        logger.info("Running reporter.")

        wait_on_event(self.shutdown)

    def on_discovery_add(self, discovery):
        """
        Added discovery method hook. Calls the `connect()` method on the new
        discovery method.
        """
        discovery.connect()

    def on_discovery_update(self, name, new_config):
        """
        Once a Discovery is updated we update each associated Service's
        `is_up` flag to None so that the next iteration of the `run_checks`
        loop does the proper reporting again.
        """
        for service in self.configurables[Service].values():
            if service.discovery == name:
                service.is_up = None

    def on_discovery_remove(self, name):
        """
        Removed discovery method hook, calls `stop()` on the removed discovery
        method.
        """
        self.configurables[Discovery][name].stop()

    def on_service_add(self, service):
        """
        When a new service is added, a worker thread is launched to
        periodically run the checks for that service.
        """
        self.pool.apply_async(self.run_checks, [service])

    def run_checks(self, service):
        """
        While the reporter is not shutting down and the service being checked
        is present in the reporter's configuration, this method will run
        all of the defined checks for the service.

        If all checks pass and the service's present node was previously
        reported as down, the present node is reportes as up.  Conversely, if
        any of the checks fail and the service's present node was previously
        reported as up, the present node will be reported as down.

        Rests for an interval defined on the service between each check
        run.
        """
        threading.currentThread().setName("%s check" % service.name)
        logger.info("Starting check run for service '%s'", service.name)

        while (
                service in self.configurables[Service].values()
                and not self.shutdown.is_set()
        ):
            logger.debug("Running checks. (%s)", service.name)

            if not service.checks:
                logger.warn("No checks defined for service: %s", service.name)
                wait_on_event(self.shutdown, timeout=service.check_interval)
                continue

            if service.discovery not in self.configurables[Discovery]:
                logger.warn(
                    "Service %s is using Unknown/unavailable discovery '%s'.",
                    service.name, service.discovery
                )
                wait_on_event(self.shutdown, timeout=service.check_interval)
                continue

            for check in service.checks.values():
                check.run()

            checks_pass = service.checks and all([
                check.passing for check in service.checks.values()
            ])

            discovery = self.configurables[Discovery][service.discovery]
            if service.is_up in (False, None) and checks_pass:
                logger.debug("Reporting service as up (%s)", service.name)
                discovery.report_up(service)
                service.is_up = True
            elif service.is_up in (True, None) and not checks_pass:
                logger.debug("Reporting service as down (%s)", service.name)
                discovery.report_down(service)
                service.is_up = False

            logger.debug("sleeping for %s seconds", service.check_interval)
            wait_on_event(self.shutdown, timeout=service.check_interval)

    def wind_down(self):
        """
        Winds down the reporter by stopping any discovery method instances.

        The various checks being run are part of the worker thread pool, which
        is taken care of in the base ConfigWatcher's `stop()` method.
        """
        for discovery in self.configurables[Discovery].values():
            discovery.stop()
        self.pool.close()
        self.pool.join()
