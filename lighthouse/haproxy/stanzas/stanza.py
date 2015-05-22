import logging

from ..directives import directives_by_section


logger = logging.getLogger(__name__)


class Stanza(object):
    """
    Subclass for config file stanzas.

    In an HAProxy config file, a stanza is in the form of::

      stanza header
          directive
          directive
          directive

    Stanza instances have a `header` attribute for the header and a list of
    `lines`, one for each directive line.
    """

    def __init__(self, section_name):
        self.section_name = section_name
        self.header = section_name
        self.lines = []

    def add_lines(self, lines):
        """
        Simple helper method for adding multiple lines at once.
        """
        for line in lines:
            self.add_line(line)

    def add_line(self, line):
        """
        Adds a given line string to the list of lines, validating the line
        first.
        """
        if not self.is_valid_line(line):
            logger.warn(
                "Invalid line for %s section: '%s'",
                self.section_name, line
            )
            return

        self.lines.append(line)

    def is_valid_line(self, line):
        """
        Validates a given line against the associated "section" (e.g. 'global'
        or 'frontend', etc.) of a stanza.

        If a line represents a directive that shouldn't be within the stanza
        it is rejected.  See the `directives.json` file for a condensed look
        at valid directives based on section.
        """
        adjusted_line = line.strip().lower()

        return any([
            adjusted_line.startswith(directive)
            for directive in directives_by_section[self.section_name]
        ])

    def __str__(self):
        """
        Returns the string representation of a Stanza, meant for use in
        config file content.

        if no lines are defined an empty string is returned.
        """
        if not self.lines:
            return ""

        return self.header + "\n" + "\n".join([
            "\t" + line
            for line in self.lines
        ])
