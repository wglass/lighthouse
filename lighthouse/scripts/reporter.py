import argparse

from lighthouse import log, reporter


parser = argparse.ArgumentParser(
    description="Lighthouse node status reporting script."
)

parser.add_argument(
    "config_dir", type=str,
    help="The directory where config files are stored."
)


def run():
    args = parser.parse_args()

    log.setup("REPORTER")

    r = reporter.Reporter(args.config_dir)

    try:
        r.start()
    except KeyboardInterrupt:
        r.stop()
