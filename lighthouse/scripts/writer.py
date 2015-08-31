import argparse
import logging

from lighthouse import log, writer


parser = argparse.ArgumentParser(
    description="Lighthouse HAProxy config writer."
)

parser.add_argument(
    "config_dir", type=str,
    help="The directory where config files are stored."
)
parser.add_argument(
    "-d", "--debug", action="store_true", default=False,
    help="Turns on debugging output."
)
parser.add_argument(
    "-l", "--log-config", type=str,
    help="Config file for the logging system."
)


def run():
    args = parser.parse_args()

    logger = log.setup("WRITER", args.log_config)

    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    w = writer.Writer(args.config_dir)

    try:
        w.start()
    except KeyboardInterrupt:
        w.stop()
