try:
    import unittest2 as unittest
except ImportError:
    import unittest

import threading

from mock import patch
from concurrent import futures


class WatcherTestCase(unittest.TestCase):

    def setUp(self):
        super(WatcherTestCase, self).setUp()

        futures_patcher = patch("lighthouse.configs.watcher.futures")
        threading_patcher = patch("lighthouse.configs.watcher.threading")

        mock_futures = futures_patcher.start()
        mock_threading = threading_patcher.start()

        self.addCleanup(futures_patcher.stop)
        self.addCleanup(threading_patcher.stop)

        def immediate_future(fn, *args, **kwargs):
            f = futures.Future()

            try:
                f.set_result(fn(*args, **kwargs))
            except Exception as e:
                f.set_exception(e)

            return f

        def immediate_thread(target, args, kwargs):
            return target(*args, **kwargs)

        mock_futures.ThreadPoolExecutor.\
            return_value.submit.side_effect = immediate_future

        mock_threading.Thread.side_effect = immediate_thread
        mock_threading.Event = threading.Event
