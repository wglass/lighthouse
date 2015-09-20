import logging
import sys
import threading

import six


logger = logging.getLogger(__name__)


def wait_on_any(*events, **kwargs):
    """
    Helper method for waiting for any of the given threading events to be
    set.

    The standard threading lib doesn't include any mechanism for waiting on
    more than one event at a time so we have to monkey patch the events
    so that their `set()` and `clear()` methods fire a callback we can use
    to determine how a composite event should react.
    """
    timeout = kwargs.get("timeout")
    composite_event = threading.Event()

    if any([event.is_set() for event in events]):
        return

    def on_change():
        if any([event.is_set() for event in events]):
            composite_event.set()
        else:
            composite_event.clear()

    def patch(original):

        def patched():
            original()
            on_change()

        return patched

    for event in events:
        event.set = patch(event.set)
        event.clear = patch(event.clear)

    wait_on_event(composite_event, timeout=timeout)


def wait_on_event(event, timeout=None):
    """
    Waits on a single threading Event, with an optional timeout.

    This is here for compatibility reasons as python 2 can't reliably wait
    on an event without a timeout and python 3 doesn't define a `maxint`.
    """
    if timeout is not None:
        event.wait(timeout)
        return

    if six.PY2:
        # Thanks to a bug in python 2's threading lib, we can't simply call
        # .wait() with no timeout since it would wind up ignoring signals.
        while not event.is_set():
            event.wait(sys.maxint)
    else:
        event.wait()
