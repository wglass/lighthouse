import logging
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from lighthouse.log import cli


@patch.object(cli, "colorama", create=True)
class LogCLITests(unittest.TestCase):

    @patch.object(cli, "color_available", True)
    def test_color_string(self, colorama):
        self.assertEqual(
            cli.color_string(colorama.Fore.BLUE, "foobar"),
            colorama.Fore.BLUE + "foobar" + colorama.Fore.RESET
        )

    @patch.object(cli, "color_available", False)
    def test_color_string_color_unavailable(self, colorama):
        self.assertEqual(
            cli.color_string(None, "foobar"),
            "foobar"
        )

    @patch.object(cli, "color_available", True)
    def test_color_for_level_debug(self, colorama):
        self.assertEqual(
            cli.color_for_level(logging.DEBUG),
            colorama.Fore.WHITE
        )

    @patch.object(cli, "color_available", True)
    def test_color_for_level_info(self, colorama):
        self.assertEqual(
            cli.color_for_level(logging.INFO),
            colorama.Fore.BLUE
        )

    @patch.object(cli, "color_available", True)
    def test_color_for_level_warning(self, colorama):
        self.assertEqual(
            cli.color_for_level(logging.WARNING),
            colorama.Fore.YELLOW
        )

    @patch.object(cli, "color_available", True)
    def test_color_for_level_error(self, colorama):
        self.assertEqual(
            cli.color_for_level(logging.ERROR),
            colorama.Fore.RED
        )

    @patch.object(cli, "color_available", True)
    def test_color_for_level_critical(self, colorama):
        self.assertEqual(
            cli.color_for_level(logging.CRITICAL),
            colorama.Fore.MAGENTA
        )

    @patch.object(cli, "color_available", True)
    def test_color_for_level_custom(self, colorama):
        self.assertEqual(
            cli.color_for_level(88),
            colorama.Fore.WHITE
        )

    @patch.object(cli, "color_available", False)
    def test_color_for_level_color_unavailable(self, colorama):
        self.assertEqual(
            cli.color_for_level(logging.CRITICAL),
            None
        )

    @patch.object(cli, "color_available", True)
    def test_thread_color_cycle(self, colorama):
        color_cycle = cli.create_thread_color_cycle()

        colors = []
        for i in range(10):
            colors.append(next(color_cycle))

        self.assertEqual(
            colors,
            [
                colorama.Fore.CYAN,
                colorama.Fore.BLUE,
                colorama.Fore.MAGENTA,
                colorama.Fore.GREEN,
                colorama.Fore.CYAN,
                colorama.Fore.BLUE,
                colorama.Fore.MAGENTA,
                colorama.Fore.GREEN,
                colorama.Fore.CYAN,
                colorama.Fore.BLUE,
            ]
        )

    @patch.object(cli, "color_available", False)
    def test_thread_color_cycle_color_unavailable(self, colorama):
        color_cycle = cli.create_thread_color_cycle()

        colors = []
        for i in range(10):
            colors.append(next(color_cycle))

        self.assertEqual(
            colors,
            [None] * 10
        )

    @patch.object(cli, "color_available", True)
    def test_color_for_thread(self, colorama):
        thread_colors_patcher = patch(
            "lighthouse.log.cli.thread_colors",
            cli.create_thread_color_cycle()
        )
        seen_thread_colors_patcher = patch(
            "lighthouse.log.cli.seen_thread_colors", {}
        )
        thread_colors_patcher.start()
        seen_thread_colors_patcher.start()
        self.addCleanup(thread_colors_patcher.stop)
        self.addCleanup(seen_thread_colors_patcher.stop)

        self.assertEqual(cli.color_for_thread("thread-10"), colorama.Fore.CYAN)
        self.assertEqual(cli.color_for_thread("thread-11"), colorama.Fore.BLUE)
        self.assertEqual(
            cli.color_for_thread("thread-12"), colorama.Fore.MAGENTA
        )
        self.assertEqual(cli.color_for_thread("thread-11"), colorama.Fore.BLUE)
        self.assertEqual(cli.color_for_thread("thread-10"), colorama.Fore.CYAN)

    @patch.object(cli, "color_available", False)
    def test_color_for_thread_color_unavailable(self, colorama):
        thread_colors_patcher = patch(
            "lighthouse.log.cli.thread_colors",
            cli.create_thread_color_cycle()
        )
        seen_thread_colors_patcher = patch(
            "lighthouse.log.cli.seen_thread_colors", {}
        )
        thread_colors_patcher.start()
        seen_thread_colors_patcher.start()
        self.addCleanup(thread_colors_patcher.stop)
        self.addCleanup(seen_thread_colors_patcher.stop)

        self.assertEqual(cli.color_for_thread("thread-10"), None)
        self.assertEqual(cli.color_for_thread("thread-11"), None)
        self.assertEqual(cli.color_for_thread("thread-12"), None)
        self.assertEqual(cli.color_for_thread("thread-11"), None)
        self.assertEqual(cli.color_for_thread("thread-10"), None)

    def test_cli_handler_tty_property(self, colorama):
        handler = cli.CLIHandler()
        self.assertEqual(handler.is_tty, True)

    @patch("lighthouse.log.cli.logging.Formatter")
    @patch.object(cli.CLIHandler, "is_tty", True)
    @patch.object(cli, "color_available", True)
    def test_cli_handler_format(self, Formatter, colorama):
        colorama.Fore.BLUE = "<BLUE>"
        colorama.Fore.CYAN = "<CYAN>"
        colorama.Fore.YELLOW = "<YELLOW>"
        colorama.Fore.RESET = "<RESET>"

        thread_colors_patcher = patch(
            "lighthouse.log.cli.thread_colors",
            cli.create_thread_color_cycle()
        )
        seen_thread_colors_patcher = patch(
            "lighthouse.log.cli.seen_thread_colors", {}
        )
        thread_colors_patcher.start()
        seen_thread_colors_patcher.start()
        self.addCleanup(thread_colors_patcher.stop)
        self.addCleanup(seen_thread_colors_patcher.stop)

        handler = cli.CLIHandler()

        record = logging.LogRecord(
            "asdf", logging.WARNING,
            "/foo/bar/bazz.py", 18,
            "Something went wrong??", (), None
        )

        self.assertEqual(
            handler.format(record), Formatter.return_value.format.return_value
        )
        Formatter.return_value.format.assert_called_once_with(record)
        Formatter.assert_called_once_with(
            '<YELLOW>[%(asctime)s W]<RESET>' +
            '<CYAN>[%(threadName)s]<RESET>' +
            ' %(message)s', '%Y-%m-%d %H:%M:%S'
        )

    @patch.object(cli.CLIHandler, "is_tty", False)
    def test_cli_handler_format_not_a_terminal(self, colorama):
        handler = cli.CLIHandler()

        record = logging.LogRecord(
            "asdf", logging.WARNING,
            "/foo/bar/bazz.py", 18,
            "Something went wrong??", (), None
        )

        self.assertEqual(
            handler.format(record),
            "Something went wrong??"
        )
