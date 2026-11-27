"""Settings read from environment variables.

Values are never hard-coded: they come from the environment, which the Makefile fills
from ``.env`` (see ``.env.example``). A missing variable is an error with a clear
message, not a silent default, so a misconfigured run stops before doing any work.
"""

from __future__ import annotations

import os
from collections.abc import Mapping


class MissingSettingError(Exception):
    """A required environment variable is not set."""


def require_env(name: str, environ: Mapping[str, str] | None = None) -> str:
    """Value of the environment variable ``name``; error if it is missing or empty.

    Args:
        name: name of the variable.
        environ: where to read it from; ``os.environ`` if not given. Tests pass a dict.
    """
    environ = os.environ if environ is None else environ
    value = environ.get(name, "").strip()
    if not value:
        raise MissingSettingError(f"{name} is not set: copy .env.example to .env and fill it in")
    return value
