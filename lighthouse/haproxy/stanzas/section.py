class Section(object):
    """
    Represents a section of HAProxy config file stanzas.

    This is used to organize generated config file content and provide header
    comments for sections describing nature of the grouped-together stanzas.
    """

    def __init__(self, heading, *stanzas):
        self.heading = heading
        self.stanzas = stanzas
        if not self.stanzas:
            self.stanzas = []

    @property
    def header(self):
        return "\n".join([
            "#",
            "# %s" % self.heading,
            "#"
        ])

    def __str__(self):
        """
        Joins together the section header and stanza strings with space
        inbetween.
        """
        stanzas = list(self.stanzas)
        if not stanzas:
            stanzas = ["# No stanzas defined for this section."]

        return "\n\n".join(map(str, [self.header] + stanzas))
