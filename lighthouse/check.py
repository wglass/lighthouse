import collections
import logging
import itertools

from .pluggable import Pluggable

logger = logging.getLogger(__name__)


class Check(Pluggable):
    """
    Base class for service check plugins.

    Subclasses are expected to define a name for the check, plus methods for
    validating that any dependencies are present, the given config is valid,
    and of course performing the check itself.
    """

    entry_point = "lighthouse.checks"

    def __init__(self):
        self.host = None
        self.port = None

        self.rise = None
        self.fall = None

        self.results = deque()
        self.passing = False

    @classmethod
    def validate_check_config(cls, config):
        """
        This method should return True if the given config is valid for the
        health check subclass, False otherwise.
        """
        raise NotImplementedError

    def apply_check_config(self, config):
        """
        This method takes an already-validated configuration dictionary as its
        only argument.

        The method should set any attributes or state in the instance needed
        for performing the health check.
        """
        raise NotImplementedError

    def perform(self):
        """
        This `perform()` is at the heart of the check.  Subclasses must define
        this method to actually perform their check.  If the check passes, the
        method should return True, otherwise False.

        Note that this method takes no arguments.  Any sort of context required
        for performing a check should be handled by the config.
        """
        raise NotImplementedError

    def run(self):
        """
        Calls the `perform()` method defined by subclasses and stores the
        result in a `results` deque.

        After the result is determined the `results` deque is analyzed to see
        if the `passing` flag should be updated.  If the check was considered
        passing and the previous `self.fall` number of checks failed, the check
        is updated to not be passing.  If the check was not passing and the
        previous `self.rise` number of checks passed, the check is updated to
        be considered passing.
        """
        logger.debug("Running %s check", self.name)

        try:
            result = self.perform()
        except Exception:
            logger.exception("Error while performing %s check", self.name)
            result = False

        logger.debug("Result: %s", result)

        self.results.append(result)
        if self.passing and not any(self.last_n_results(self.fall)):
            logger.info(
                "%s check failed %d time(s), no longer passing.",
                self.name, self.fall,
            )
            self.passing = False
        if not self.passing and all(self.last_n_results(self.rise)):
            logger.info(
                "%s check passed %d time(s), is now passing.",
                self.name, self.rise
            )
            self.passing = True

    def last_n_results(self, n):
        """
        Helper method for returning a set number of the previous check results.
        """
        return list(
            itertools.islice(
                self.results, len(self.results) - n, len(self.results)
            )
        )

    def apply_config(self, config):
        """
        Sets attributes based on the given config.

        Also adjusts the `results` deque to either expand (padding itself with
        False results) or contract (by removing the oldest results) until it
        matches the required length.
        """
        self.rise = int(config["rise"])
        self.fall = int(config["fall"])

        self.apply_check_config(config)

        if self.results.maxlen == max(self.rise, self.fall):
            return

        results = list(self.results)
        while len(results) > max(self.rise, self.fall):
            results.pop(0)
        while len(results) < max(self.rise, self.fall):
            results.insert(0, False)

        self.results = deque(
            results,
            maxlen=max(self.rise, self.fall)
        )

    @classmethod
    def validate_config(cls, config):
        """
        Validates that required config entries are present.

        Each check requires a `host`, `port`, `rise` and `fall` to be
        configured.

        The rise and fall variables are integers denoting how many times a
        check must pass before being considered passing and how many times a
        check must fail before being considered failing.
        """
        if "rise" not in config:
            raise ValueError("No 'rise' configured")
        if "fall" not in config:
            raise ValueError("No 'fall' configured")

        cls.validate_check_config(config)


class deque(collections.deque):
    """
    Custom collections.deque subclass for 2.6 compatibility.

    The python 2.6 version of the deque class doesn't support referring to
    the `maxlen` attribute.
    """

    def __init__(self, iterable=(), maxlen=None):
        self._maxlen = maxlen
        super(deque, self).__init__(iterable=iterable, maxlen=maxlen)

    @property
    def maxlen(self):
        return self._maxlen
