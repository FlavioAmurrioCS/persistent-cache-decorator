from __future__ import annotations


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    args = parser.parse_args(argv)
    print(f"Arguments: {vars(args)=}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
