try:
    import unittest2 as unittest
except ImportError:
    import unittest

from lighthouse.haproxy.stanzas.stanza import Stanza
from lighthouse.haproxy.stanzas.section import Section


class SectionTests(unittest.TestCase):

    def test_no_stanzas(self):
        section = Section("A Section")

        self.assertTrue(
            "# No stanzas defined for this section." in str(section)
        )

    def test_heading(self):
        section = Section("This is a section, ok")

        self.assertTrue(
            str(section).startswith(
                "#\n"
                + "# This is a section, ok\n"
                + "#\n"
                + "\n"
            )
        )

    def test_stanzas(self):
        stanza1 = Stanza("front")
        stanza1.lines = ["foo bar", "thing guy"]
        stanza2 = Stanza("back")
        stanza2.lines = ["reticulate_splines=true"]

        section = Section(
            "A Section",
            stanza1, stanza2
        )

        self.assertEqual(
            str(section).replace("\t", "    "),
            """#
# A Section
#

front
    foo bar
    thing guy

back
    reticulate_splines=true"""
        )
