"""Download a file over HTTP to local disk, safely and politely.

The body is streamed in chunks to a temporary ``<name>.part`` file, and the file is
renamed to its final name only when it is complete. A file with its final name is
therefore always a whole file, which makes the download idempotent: if the final file
exists, it is not downloaded again.

Transient failures (timeouts, dropped connections, HTTP 429 and 5xx, an incomplete
body) are retried with exponential backoff. The whole download is retried, not only
the request, so a connection that drops halfway through the body is covered too. A
wait asked by the server with ``Retry-After`` is honoured up to a limit; above it the
download stops with ``SourceUnavailableError`` instead of blocking for a long time.

Two runs can download the same file at the same time, for example when an Airflow
retry starts while the first try is still running. They would share the ``.part``
file and mix their bytes, so each download holds an exclusive lock on a
``<name>.lock`` file next to it. The second run waits for the first one, then finds
the final file and skips it, without a second request to the source.
"""

from __future__ import annotations

import email.utils
import fcntl
import hashlib
import logging
import os
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# HTTP statuses that mean "try again later": too many requests and server-side errors.
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

# Network errors worth retrying. ChunkedEncodingError is what requests raises when the
# connection drops while the body is being read.
RETRYABLE_EXCEPTIONS = (
    requests.ConnectionError,
    requests.Timeout,
    requests.exceptions.ChunkedEncodingError,
)

DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1 MiB


class DownloadError(Exception):
    """The file could not be downloaded."""


class SourceUnavailableError(DownloadError):
    """The source is temporarily unavailable: the download can be tried again later."""


class _TransientError(Exception):
    """A failure that is worth retrying, with the wait asked by the server, if any."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


@dataclass(frozen=True)
class RetryPolicy:
    """How many times to try a download and how long to wait between attempts."""

    max_attempts: int = 5
    backoff_initial: float = 2.0
    backoff_max: float = 60.0
    max_retry_after: float = 300.0

    def backoff(self, attempt: int) -> float:
        """Seconds to wait after failed attempt number ``attempt`` (starting at 1).

        The wait doubles at every attempt (2, 4, 8, ... seconds) up to ``backoff_max``.
        """
        return min(self.backoff_max, self.backoff_initial * 2 ** (attempt - 1))


@dataclass(frozen=True)
class DownloadResult:
    """What was downloaded, for the snapshot manifest."""

    url: str
    path: Path
    size_bytes: int
    sha256: str
    downloaded: bool  # False when the file already existed and was skipped


def download_file(
    session: requests.Session,
    url: str,
    dest: Path,
    *,
    timeout: float = 30.0,
    retry: RetryPolicy | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    sleep: Callable[[float], None] = time.sleep,
) -> DownloadResult:
    """Download ``url`` to ``dest``, unless ``dest`` already exists.

    If another process is downloading the same ``dest``, wait for it to finish.

    Args:
        session: HTTP session, so that connections and headers are shared across calls.
        url: address of the file.
        dest: final path of the file. Parent folders are created if needed.
        timeout: seconds to wait for the server to connect or send data.
        retry: retry policy; the defaults of ``RetryPolicy`` if not given.
        chunk_size: bytes read and written at a time.
        sleep: function used to wait between attempts. Tests replace it so that they
            do not actually wait.

    Raises:
        SourceUnavailableError: the source kept failing with transient errors, or asked
            to wait longer than ``retry.max_retry_after``.
        DownloadError: a permanent failure, such as HTTP 404; it is not retried.
    """
    retry = retry or RetryPolicy()

    # Fast path without the lock: a file with its final name is always complete.
    if dest.exists():
        return _skip(url, dest, chunk_size)

    dest.parent.mkdir(parents=True, exist_ok=True)
    with _exclusive_lock(dest.with_name(dest.name + ".lock")):
        # Check again: another run may have finished the file while we waited.
        if dest.exists():
            return _skip(url, dest, chunk_size)
        return _download_with_retry(session, url, dest, timeout, retry, chunk_size, sleep)


def _download_with_retry(
    session: requests.Session,
    url: str,
    dest: Path,
    timeout: float,
    retry: RetryPolicy,
    chunk_size: int,
    sleep: Callable[[float], None],
) -> DownloadResult:
    """The retry loop of ``download_file``; the caller holds the lock on ``dest``."""
    part = dest.with_name(dest.name + ".part")

    for attempt in range(1, retry.max_attempts + 1):
        try:
            size, digest = _stream_to_file(session, url, part, timeout, chunk_size)
        except _TransientError as exc:
            part.unlink(missing_ok=True)
            if exc.retry_after is not None and exc.retry_after > retry.max_retry_after:
                raise SourceUnavailableError(
                    f"{url}: the server asked to retry after {exc.retry_after:.0f} s, "
                    f"more than the limit of {retry.max_retry_after:.0f} s"
                ) from exc
            if attempt == retry.max_attempts:
                raise SourceUnavailableError(
                    f"{url}: still failing after {attempt} attempts: {exc}"
                ) from exc
            wait = max(retry.backoff(attempt), exc.retry_after or 0.0)
            logger.warning(
                "Attempt %d/%d for %s failed (%s); retrying in %.1f s",
                attempt,
                retry.max_attempts,
                url,
                exc,
                wait,
            )
            sleep(wait)
        except BaseException:
            # Permanent errors, and also Ctrl+C: never leave a half-written file behind.
            part.unlink(missing_ok=True)
            raise
        else:
            part.replace(dest)
            logger.info("Downloaded %s to %s (%d bytes)", url, dest, size)
            return DownloadResult(url, dest, size, digest, downloaded=True)

    raise AssertionError("unreachable: the last attempt either returns or raises")


def _skip(url: str, dest: Path, chunk_size: int) -> DownloadResult:
    """Result for a file that already exists, which is not downloaded again."""
    size, digest = _file_stats(dest, chunk_size)
    logger.info("Skipping %s: %s already exists", url, dest)
    return DownloadResult(url, dest, size, digest, downloaded=False)


@contextmanager
def _exclusive_lock(path: Path) -> Iterator[None]:
    """Hold an exclusive ``flock`` on ``path``, waiting if another process holds it.

    The kernel releases the lock when the file is closed, also when the process is
    killed, so a crash never leaves a stale lock. The lock file is left in place on
    purpose: deleting it while another process waits on it would let a third process
    lock a new file with the same name, and two downloads would run at once again.
    """
    with path.open("a") as file:
        try:
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            logger.info("Waiting for another download holding %s", path)
            fcntl.flock(file, fcntl.LOCK_EX)
        yield


def parse_retry_after(value: str | None, now: datetime | None = None) -> float | None:
    """Seconds to wait according to a ``Retry-After`` header, or None if unusable.

    The header is either a number of seconds (``"120"``) or an HTTP date
    (``"Wed, 18 Nov 2026 10:00:00 GMT"``). A date in the past means "no wait".
    """
    if value is None:
        return None
    value = value.strip()
    # isdecimal, not isdigit: isdigit accepts characters such as "²" that float()
    # cannot parse.
    if value.isdecimal():
        return float(value)
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    now = now or datetime.now(UTC)
    return max(0.0, (when - now).total_seconds())


def _stream_to_file(
    session: requests.Session, url: str, part: Path, timeout: float, chunk_size: int
) -> tuple[int, str]:
    """Write the body of ``url`` to ``part``; return its size and SHA-256."""
    try:
        with session.get(url, stream=True, timeout=timeout) as response:
            if response.status_code in RETRYABLE_STATUS_CODES:
                raise _TransientError(
                    f"HTTP {response.status_code}",
                    parse_retry_after(response.headers.get("Retry-After")),
                )
            if response.status_code != 200:
                raise DownloadError(f"{url}: HTTP {response.status_code}, not retrying")

            expected = _expected_size(response)
            digest = hashlib.sha256()
            size = 0
            with part.open("wb") as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    file.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
                # Make the bytes durable before the rename in the caller: otherwise,
                # after a power cut, the rename could survive and the data not.
                file.flush()
                os.fsync(file.fileno())
    except RETRYABLE_EXCEPTIONS as exc:
        raise _TransientError(f"{type(exc).__name__}: {exc}") from exc

    if expected is not None and size != expected:
        raise _TransientError(f"incomplete body: received {size} of {expected} bytes")
    return size, digest.hexdigest()


def _expected_size(response: requests.Response) -> int | None:
    """Body size announced by the server, if it can be compared with what we write.

    When the server compresses the transfer (``Content-Encoding: gzip``), requests
    decompresses the chunks, so ``Content-Length`` (the compressed size) no longer
    matches the bytes written and cannot be used.
    """
    if response.headers.get("Content-Encoding", "identity") != "identity":
        return None
    length = response.headers.get("Content-Length")
    return int(length) if length is not None and length.isdecimal() else None


def _file_stats(path: Path, chunk_size: int) -> tuple[int, str]:
    """Size and SHA-256 of a file on disk, read in chunks."""
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)
            size += len(chunk)
    return size, digest.hexdigest()
