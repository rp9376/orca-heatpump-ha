"""Serve a dump fixture as a fake display: python -m tools.emulator DUMP."""

import argparse
from pathlib import Path

from aiohttp import web

from .server import Emulator


def main() -> None:
    """Run the emulator until interrupted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", type=Path, help="a tests/fixtures/dumps JSON file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8780)
    parser.add_argument(
        "--writable", action="store_true", help="accept writes to every tag"
    )
    args = parser.parse_args()
    emulator = Emulator.from_dump(args.dump)
    if args.writable:
        emulator.writable = set(emulator.values)
    web.run_app(emulator.app, host=args.host, port=args.port)


main()
