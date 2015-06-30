import logging

from .pluggable import Pluggable


logger = logging.getLogger(__name__)


class Coordinator(Pluggable):
    """
    Base class for coordinator definitions.

    The complexity of generating valid configuration content and updating
    the proper file(s) is left as details for subclasses so this base class
    remains incredibly simple.

    All subclasses are expected to implement a `sync_file` method that is
    called whenever an update to the topography of nodes happens.
    """

    entry_point = "lighthouse.coordinators"

    def sync_file(self, clusters):
        """
        This method must take a list of clusters and update any and all
        relevant configuration files with valid config content for coordinating
        and/or balancing load for the given clusters.
        """
        raise NotImplementedError
