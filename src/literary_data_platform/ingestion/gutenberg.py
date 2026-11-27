"""Download the Project Gutenberg catalogue from a mirror into the raw layer.

Only the CSV catalogue is downloaded (decision D11). It is stored as it arrives,
still gzip-compressed, under the date of the download (decision D12)::

    $DATA_DIR/raw/gutenberg/<YYYY-MM-DD>/pg_catalog.csv.gz

Running again on the same date skips the file; running on another date stores a new
copy. Run it with ``make gutenberg-catalog`` or::

    python -m literary_data_platform.ingestion.gutenberg [--date YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from pathlib import Path

import requests

from literary_data_platform.config import MissingSettingError, require_env
from literary_data_platform.ingestion.download import DownloadError, DownloadResult, download_file

logger = logging.getLogger(__name__)

# Where the catalogue lives on every Project Gutenberg mirror, and its file name.
CATALOG_PATH_ON_MIRROR = "cache/epub/feeds/pg_catalog.csv.gz"
CATALOG_FILE_NAME = "pg_catalog.csv.gz"


def catalog_url(mirror_url: str) -> str:
    """URL of the catalogue on a mirror, with or without a trailing slash."""
    return f"{mirror_url.rstrip('/')}/{CATALOG_PATH_ON_MIRROR}"


def catalog_path(data_dir: Path, snapshot: date) -> Path:
    """Path of the catalogue in the raw layer for a snapshot date."""
    return data_dir / "raw" / "gutenberg" / snapshot.isoformat() / CATALOG_FILE_NAME


def download_catalog(
    session: requests.Session, mirror_url: str, data_dir: Path, snapshot: date
) -> DownloadResult:
    """Download the catalogue for ``snapshot``, unless it is already there."""
    return download_file(session, catalog_url(mirror_url), catalog_path(data_dir, snapshot))


def main(argv: Sequence[str] | None = None, environ: Mapping[str, str] | None = None) -> int:
    """Command line entry point. Returns the process exit code: 0 on success, 1 on error."""
    parser = argparse.ArgumentParser(description="Download the Project Gutenberg catalogue.")
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=None,
        help="snapshot date, YYYY-MM-DD (default: today, UTC)",
    )
    args = parser.parse_args(argv)
    snapshot = args.date or datetime.now(UTC).date()

    try:
        data_dir = Path(require_env("DATA_DIR", environ))
        mirror_url = require_env("GUTENBERG_MIRROR_URL", environ)
        user_agent = require_env("HTTP_USER_AGENT", environ)
    except MissingSettingError as exc:
        logger.error("%s", exc)
        return 1

    with requests.Session() as session:
        session.headers["User-Agent"] = user_agent
        try:
            result = download_catalog(session, mirror_url, data_dir, snapshot)
        except DownloadError as exc:
            logger.error("Catalogue not downloaded: %s", exc)
            return 1

    logger.info(
        "Catalogue %s: %s (%d bytes, sha256 %s)",
        "downloaded" if result.downloaded else "already present",
        result.path,
        result.size_bytes,
        result.sha256,
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    raise SystemExit(main())
