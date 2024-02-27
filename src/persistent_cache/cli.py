from __future__ import annotations

import argparse
import os
import subprocess
from typing import Sequence

from persistent_cache.decorators import sqlite_cache


def run_cli_helper(cmd: tuple[str, ...] | list[str], cwd: str | None = None) -> str:
    try:
        result = subprocess.run(
            args=cmd,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            errors="ignore",
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as e:
        raise SystemExit(e.returncode) from None
    return result.stdout


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--include-dir", action="store_true", help="Include directory")
    parser.add_argument("--minutes", type=int, default=60, help="Cache duration in minutes")
    parser.add_argument("cmd", nargs="+", help="Command to run")
    args = parser.parse_args(argv)

    cached_func = sqlite_cache(minutes=args.minutes)(run_cli_helper)
    result = cached_func(cmd=args.cmd, cwd=os.getcwd() if args.include_dir else None)
    print(result)
    return 0


if __name__ == "__main__":
    main()
