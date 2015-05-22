try:
    import unittest2 as unittest
except ImportError:
    import unittest

from lighthouse.haproxy.stanzas.stats import StatsStanza


class StatsStanzaTests(unittest.TestCase):

    def test_default_uri(self):
        stanza = StatsStanza(9000)

        self.assertEqual(
            str(stanza),
            """listen stats :9000
\tmode http
\tstats enable
\tstats uri /"""
        )

    def test_custom_uri(self):
        stanza = StatsStanza(9000, uri="/stats")

        self.assertEqual(
            str(stanza),
            """listen stats :9000
\tmode http
\tstats enable
\tstats uri /stats"""
        )
