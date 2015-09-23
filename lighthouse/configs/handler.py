import logging
import os

import yaml

from watchdog import events


logger = logging.getLogger(__name__)


class ConfigFileChangeHandler(events.PatternMatchingEventHandler):
    """
    Config file change event handler.

    A subclass of watchdog's PatternMatchingEventHandler.  This class takes
    callbacks for on_(add|update|delete).

    When an event comes in the proper callback is fired with processed inputs.
    """

    patterns = ("*.yaml", "*.yml")

    def __init__(
        self, target_class, on_add, on_update, on_delete,
        *args, **kwargs
    ):
        self.target_class = target_class
        self.on_add = on_add
        self.on_update = on_update
        self.on_delete = on_delete

        super(ConfigFileChangeHandler, self).__init__(*args, **kwargs)

    def file_name(self, event):
        """
        Helper method for determining the basename of the affected file.
        """
        name = os.path.basename(event.src_path)
        name = name.replace(".yaml", "")
        name = name.replace(".yml", "")

        return name

    def on_created(self, event):
        """
        Newly created config file handler.

        Parses the file's yaml contents and creates a new instance of the
        target_class with the results.  Fires the on_add callback with the
        new instance.
        """
        if os.path.isdir(event.src_path):
            return

        logger.debug("File created: %s", event.src_path)

        name = self.file_name(event)

        try:
            result = self.target_class.from_config(
                name, yaml.load(open(event.src_path))
            )
        except Exception as e:
            logger.exception(
                "Error when loading new config file %s: %s",
                event.src_path, str(e)
            )
            return

        if not result:
            return

        self.on_add(self.target_class, name, result)

    def on_modified(self, event):
        """
        Modified config file handler.

        If a config file is modified, the yaml contents are parsed and the
        new results are validated by the target class.  Once validated, the
        new config is passed to the on_update callback.
        """
        if os.path.isdir(event.src_path):
            return

        logger.debug("file modified: %s", event.src_path)

        name = self.file_name(event)

        try:
            config = yaml.load(open(event.src_path))
            self.target_class.from_config(name, config)
        except Exception:
            logger.exception(
                "Error when loading updated config file %s", event.src_path,
            )
            return

        self.on_update(self.target_class, name, config)

    def on_deleted(self, event):
        """
        Deleted config file handler.

        Simply fires the on_delete callback with the name of the deleted item.
        """
        logger.debug("file removed: %s", event.src_path)
        name = self.file_name(event)

        self.on_delete(self.target_class, name)

    def on_moved(self, event):
        """
        A move event is just proxied to an on_deleted call followed by
        an on_created call.
        """
        self.on_deleted(events.FileDeletedEvent(event.src_path))
        self.on_created(events.FileCreatedEvent(event.dest_path))
