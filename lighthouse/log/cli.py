import itertools
import logging

try:
    import colorama
    color_available = True  # pragma: no cover
except ImportError:
    color_available = False


def color_string(color, string):
    """
    Colorizes a given string, if coloring is available.
    """
    if not color_available:
        return string

    return color + string + colorama.Fore.RESET


def color_for_level(level):
    """
    Returns the colorama Fore color for a given log level.

    If color is not available, returns None.
    """
    if not color_available:
        return None

    return {
        logging.DEBUG: colorama.Fore.WHITE,
        logging.INFO: colorama.Fore.BLUE,
        logging.WARNING: colorama.Fore.YELLOW,
        logging.ERROR: colorama.Fore.RED,
        logging.CRITICAL: colorama.Fore.MAGENTA
    }.get(level, colorama.Fore.WHITE)


def create_thread_color_cycle():
    """
    Generates a never-ending cycle of colors to choose from for individual
    threads.

    If color is not available, a cycle that repeats None every time is
    returned instead.
    """
    if not color_available:
        return itertools.cycle([None])

    return itertools.cycle(
        (
            colorama.Fore.CYAN,
            colorama.Fore.BLUE,
            colorama.Fore.MAGENTA,
            colorama.Fore.GREEN,
        )
    )


thread_colors = create_thread_color_cycle()
seen_thread_colors = {}


def color_for_thread(thread_id):
    """
    Associates the thread ID with the next color in the `thread_colors` cycle,
    so that thread-specific parts of a log have a consistent separate color.
    """
    if thread_id not in seen_thread_colors:
        seen_thread_colors[thread_id] = next(thread_colors)

    return seen_thread_colors[thread_id]


class CLIHandler(logging.StreamHandler, object):
    """
    Specialized StreamHandler that provides color output if the output is a
    terminal and the colorama library is available.
    """

    @property
    def is_tty(self):
        "Returns true if the handler's stream is a terminal."
        isatty = getattr(self.stream, 'isatty', None)
        return isatty and isatty()

    def format(self, record):
        """
        Formats a given log record to include the timestamp, log level, thread
        ID and message.  Colorized if coloring is available.
        """
        if not self.is_tty:
            return super(CLIHandler, self).format(record)

        level_abbrev = record.levelname[0]

        time_and_level = color_string(
            color_for_level(record.levelno),
            "[%(asctime)s " + level_abbrev + "]"
        )
        thread = color_string(
            color_for_thread(record.thread),
            "[%(threadName)s]"
        )
        formatter = logging.Formatter(
            time_and_level + thread + " %(message)s", "%Y-%m-%d %H:%M:%S"
        )

        return formatter.format(record)
