try:
    import unittest2 as unittest
except ImportError:
    import unittest

from lighthouse.haproxy.stanzas.stanza import Stanza


class BaseStanzaTests(unittest.TestCase):

    def test_no_lines(self):
        stanza = Stanza("frontend")

        self.assertEqual(
            str(stanza), ""
        )
