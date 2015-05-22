import threading
try:
    import unittest2 as unittest
except ImportError:
    import unittest


from mock import patch, Mock

from lighthouse import events


class EventsTests(unittest.TestCase):

    @patch.object(events, "wait_on_event")
    def test_any_sub_event_set_sets_composite_event(self, wait_on_event):
        event1 = threading.Event()
        event2 = threading.Event()
        event3 = threading.Event()

        events.wait_on_any(event1, event2, event3)

        wait_args, _ = wait_on_event.call_args
        composite = wait_args[0]

        self.assertEqual(composite.is_set(), False)

        event2.set()

        self.assertEqual(composite.is_set(), True)

    @patch.object(events, "wait_on_event")
    def test_all_sub_events_clear_for_composite_to_clear(self, wait_on_event):
        event1 = threading.Event()
        event2 = threading.Event()
        event3 = threading.Event()

        events.wait_on_any(event1, event2, event3)

        wait_args, _ = wait_on_event.call_args
        composite = wait_args[0]

        self.assertEqual(composite.is_set(), False)

        event2.set()
        event3.set()

        self.assertEqual(composite.is_set(), True)

        event2.clear()

        self.assertEqual(composite.is_set(), True)

        event3.clear()

        self.assertEqual(composite.is_set(), False)

    def test_wait_on_event_with_timeout(self):
        mock_event = Mock()

        events.wait_on_event(mock_event, timeout=60)

        mock_event.wait.assert_called_once_with(60)

    @patch("lighthouse.events.six")
    def test_wait_on_event_uses_no_timeout_on_py3(self, mock_six):
        mock_six.PY2 = False

        mock_event = Mock()

        events.wait_on_event(mock_event)

        mock_event.wait.assert_called_once_with()
