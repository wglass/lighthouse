import logging

from .configs.watcher import ConfigWatcher
from .log.config import Logging
from .discovery import Discovery
from .service import Service
from .events import wait_on_event


logger = logging.getLogger(__name__)


class Reporter(ConfigWatcher):
    """
    The service node reporting class.

    This config watcher manages Discovery and Service configurable items.  For
    every service configured, a thread is created that periodically runs the
    service's checks and reports the current node as up or down to the
    service's chosen discovery method.
    """

    watched_configurables = (Logging, Discovery, Service)

    def on_discovery_add(self, discovery):
        """
        Added discovery method hook. Calls the `connect()` method on the new
        discovery method.
        """
        discovery.connect()

    def on_discovery_update(self, name, new_config):
        """
        Once a Discovery is updated we update each associated Service to reset
        its up/down status so that the next iteration of the `check_loop`
        loop does the proper reporting again.
        """
        for service in self.configurables[Service].values():
            if service.discovery == name:
                service.reset_status()

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
        self.launch_thread(service.name, self.check_loop, service)

    def on_service_remove(self, name):
        """
        If a service is removed, the associated check loop thread is killed.
        """
        self.kill_thread(name)

    def check_loop(self, service):
        """
        While the reporter is not shutting down and the service being checked
        is present in the reporter's configuration, this method will launch a
        job to run all of the service's checks and then pause for the
        configured interval.
        """
        logger.info("Starting check loop for service '%s'", service.name)

        def handle_checks_result(f):
            try:
                came_up, went_down = f.result()
            except Exception:
                logger.exception("Error checking service '%s'", service.name)
                return

            if not came_up and not went_down:
                return

            discovery = self.configurables[Discovery][service.discovery]

            for port in came_up:
                logger.debug("Reporting %s, port %d up", service.name, port)
                discovery.report_up(service, port)
            for port in went_down:
                logger.debug("Reporting %s, port %d down", service.name, port)
                discovery.report_down(service, port)

        while (
                service in self.configurables[Service].values() and
                not self.shutdown.is_set()
        ):
            self.work_pool.submit(
                self.run_checks, service
            ).add_done_callback(
                handle_checks_result
            )

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
            return set(), set()

        service.update_ports()

        came_up, went_down = service.run_checks()

        return came_up, went_down

    def wind_down(self):
        """
        Winds down the reporter by stopping any discovery method instances and
        joining any running threads.

        The base ConfigWatcher's `stop()` method sets the shutdown event so
        each check loop thread should eventually stop cleanly.
        """
        for discovery in self.configurables[Discovery].values():
            discovery.stop()
