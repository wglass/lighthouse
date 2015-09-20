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

    @patch.object(events, "wait_on_event")
    def test_wait_on_any_with_timeout(self, wait_on_event):
        event1 = Mock()
        event1.is_set.return_value = False
        event2 = Mock()
        event2.is_set.return_value = False

        events.wait_on_any(event1, event2, timeout=20)

        _, wait_kwargs = wait_on_event.call_args

        self.assertEqual(wait_kwargs["timeout"], 20)

    @patch.object(events, "wait_on_event")
    def test_wait_on_any_shortcircuits_if_already_set(self, wait_on_event):
        event1 = Mock()
        event1.is_set.return_value = True
        event2 = Mock()
        event2.is_set.return_value = False

        events.wait_on_any(event1, event2, timeout=20)

        assert wait_on_event.called is False
