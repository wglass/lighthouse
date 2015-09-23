import argparse

from lighthouse import log, writer


parser = argparse.ArgumentParser(
    description="Lighthouse HAProxy config writer."
)

parser.add_argument(
    "config_dir", type=str,
    help="The directory where config files are stored."
)


def run():
    args = parser.parse_args()

    log.setup("WRITER")

    w = writer.Writer(args.config_dir)

    try:
        w.start()
    except KeyboardInterrupt:
        w.stop()
