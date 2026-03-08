"""Module entrypoint for ``python -m universal_site_proxy``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
