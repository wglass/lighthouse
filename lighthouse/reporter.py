import logging
import threading
from concurrent import futures

from .configs.watcher import ConfigWatcher
from .discovery import Discovery
from .service import Service
from .events import wait_on_event


MAX_WORKER_THREADS = 8

logger = logging.getLogger(__name__)


class Reporter(ConfigWatcher):
    """
    The service node reporting class.

    This config watcher manages Discovery and Service configurable items.  For
    every service configured, a thread is created that periodically runs the
    service's checks and reports the current node as up or down to the
    service's chosen discovery method.
    """

    watched_configurables = (Discovery, Service)

    def __init__(self, *args, **kwargs):
        super(Reporter, self).__init__(*args, **kwargs)

        self.check_threads = {}
        self.pool = futures.ThreadPoolExecutor(max_workers=MAX_WORKER_THREADS)

    def run(self):
        """
        Since each check loop the reporter runs is a separate thread the main
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
        self.check_threads[service.name] = threading.Thread(
            target=self.check_loop,
            args=(service,)
        )
        self.check_threads[service.name].start()

    def on_service_remove(self, name):
        """
        If a service is removed, the associated check loop thread is joined
        and removed from the `check_threads` dictionary.
        """
        self.check_threads[name].join()
        del self.check_threads[name]

    def check_loop(self, service):
        """
        While the reporter is not shutting down and the service being checked
        is present in the reporter's configuration, this method will launch a
        job to run all of the service's checks and then pause for the
        configured interval.
        """
        threading.currentThread().setName("%s check loop" % service.name)
        logger.info("Starting check loop for service '%s'", service.name)

        while (
                service in self.configurables[Service].values()
                and not self.shutdown.is_set()
        ):
            self.pool.submit(self.run_checks, service)

            logger.debug("sleeping for %s seconds", service.check_interval)
            wait_on_event(self.shutdown, timeout=service.check_interval)

    def run_checks(self, service):
        """
        Runs each check for the service and reports to the service's discovery
        method based on the results.

        If all checks pass and the service's present node was previously
        reported as down, the present node is reported as up.  Conversely, if
        any of the checks fail and the service's present node was previously
        reported as up, the present node will be reported as down.
        """
        logger.debug("Running checks. (%s)", service.name)

        if service.discovery not in self.configurables[Discovery]:
            logger.warn(
                "Service %s is using Unknown/unavailable discovery '%s'.",
                service.name, service.discovery
            )
            return

        for check in service.checks.values():
            check.run()

        checks_pass = service.checks and all([
            check.passing for check in service.checks.values()
        ])

        if not service.checks:
            logger.warn("No checks defined for service: %s", service.name)
            checks_pass = True

        discovery = self.configurables[Discovery][service.discovery]
        if service.is_up in (False, None) and checks_pass:
            logger.debug("Reporting service as up (%s)", service.name)
            discovery.report_up(service)
            service.is_up = True
        elif service.is_up in (True, None) and not checks_pass:
            logger.debug("Reporting service as down (%s)", service.name)
            discovery.report_down(service)
            service.is_up = False

    def wind_down(self):
        """
        Winds down the reporter by stopping any discovery method instances and
        joining any running threads.

        The base ConfigWatcher's `stop()` method sets the shutdown event so
        each check loop thread should eventually stop cleanly.
        """
        for discovery in self.configurables[Discovery].values():
            discovery.stop()
        for thread in self.check_threads.values():
            thread.join()

        self.pool.shutdown()
