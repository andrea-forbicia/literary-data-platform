import fcntl
import gzip
import hashlib
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest
import requests
import responses
from responses.registries import OrderedRegistry

from literary_data_platform.ingestion import download
from literary_data_platform.ingestion.download import (
    DownloadError,
    RetryPolicy,
    SourceUnavailableError,
    download_file,
    parse_retry_after,
)

URL = "https://mirror.example.org/files/book.txt"
BODY = b"It is a truth universally acknowledged...\n" * 100
POLICY = RetryPolicy(max_attempts=3, backoff_initial=2.0, backoff_max=60.0, max_retry_after=30.0)


@pytest.fixture
def mocked():
    """Intercept HTTP calls made by requests. Responses are served in registration
    order, and the test fails if a registered response is never requested."""
    with responses.RequestsMock(registry=OrderedRegistry) as rsps:
        yield rsps


@pytest.fixture
def waits() -> list[float]:
    """Records the waits between attempts instead of really sleeping."""
    return []


def fetch(dest: Path, waits: list[float]):
    with requests.Session() as session:
        return download_file(session, URL, dest, retry=POLICY, sleep=waits.append)


def names(folder: Path) -> list[str]:
    return sorted(p.name for p in folder.iterdir())


def test_downloads_file_with_size_and_checksum(mocked, waits, tmp_path):
    mocked.get(URL, body=BODY)
    dest = tmp_path / "raw" / "book.txt"

    result = fetch(dest, waits)

    assert dest.read_bytes() == BODY
    assert result.downloaded is True
    assert result.size_bytes == len(BODY)
    assert result.sha256 == hashlib.sha256(BODY).hexdigest()
    assert not (tmp_path / "raw" / "book.txt.part").exists()
    assert waits == []


def test_second_run_skips_existing_file(mocked, waits, tmp_path):
    mocked.get(URL, body=BODY)
    dest = tmp_path / "book.txt"
    first = fetch(dest, waits)

    second = fetch(dest, waits)

    assert len(mocked.calls) == 1  # no second request
    assert second.downloaded is False
    assert second.sha256 == first.sha256


def test_leftover_part_file_is_overwritten(mocked, waits, tmp_path):
    (tmp_path / "book.txt.part").write_bytes(b"half a file from a crashed run")
    mocked.get(URL, body=BODY)

    fetch(tmp_path / "book.txt", waits)

    assert (tmp_path / "book.txt").read_bytes() == BODY
    assert not (tmp_path / "book.txt.part").exists()


def test_retries_server_errors_with_exponential_backoff(mocked, waits, tmp_path):
    mocked.get(URL, status=503)
    mocked.get(URL, status=502)
    mocked.get(URL, body=BODY)

    result = fetch(tmp_path / "book.txt", waits)

    assert result.downloaded is True
    assert waits == [2.0, 4.0]


def test_honours_retry_after_when_longer_than_backoff(mocked, waits, tmp_path):
    mocked.get(URL, status=429, headers={"Retry-After": "7"})
    mocked.get(URL, body=BODY)

    fetch(tmp_path / "book.txt", waits)

    assert waits == [7.0]


def test_gives_up_at_once_when_retry_after_is_above_limit(mocked, waits, tmp_path):
    mocked.get(URL, status=503, headers={"Retry-After": "3600"})

    with pytest.raises(SourceUnavailableError, match="3600"):
        fetch(tmp_path / "book.txt", waits)

    assert waits == []
    assert names(tmp_path) == ["book.txt.lock"]


def test_gives_up_after_max_attempts(mocked, waits, tmp_path):
    for _ in range(POLICY.max_attempts):
        mocked.get(URL, status=500)

    with pytest.raises(SourceUnavailableError, match="3 attempts"):
        fetch(tmp_path / "book.txt", waits)

    assert len(mocked.calls) == POLICY.max_attempts
    assert waits == [2.0, 4.0]
    assert names(tmp_path) == ["book.txt.lock"]


def test_does_not_retry_not_found(mocked, waits, tmp_path):
    mocked.get(URL, status=404)

    with pytest.raises(DownloadError, match="404") as excinfo:
        fetch(tmp_path / "book.txt", waits)

    assert not isinstance(excinfo.value, SourceUnavailableError)
    assert len(mocked.calls) == 1
    assert names(tmp_path) == ["book.txt.lock"]


def test_retries_connection_error(mocked, waits, tmp_path):
    mocked.get(URL, body=requests.ConnectionError("connection reset"))
    mocked.get(URL, body=BODY)

    result = fetch(tmp_path / "book.txt", waits)

    assert result.downloaded is True
    assert waits == [2.0]


def test_retries_body_shorter_than_content_length(mocked, waits, tmp_path):
    # The connection "drops" after a few bytes: fewer bytes than announced arrive.
    mocked.get(URL, body=BODY[:10], headers={"Content-Length": str(len(BODY))})
    mocked.get(URL, body=BODY)

    result = fetch(tmp_path / "book.txt", waits)

    assert (tmp_path / "book.txt").read_bytes() == BODY
    assert result.size_bytes == len(BODY)
    assert waits == [2.0]


def test_backoff_doubles_and_is_capped():
    policy = RetryPolicy(backoff_initial=2.0, backoff_max=10.0)

    assert [policy.backoff(n) for n in range(1, 6)] == [2.0, 4.0, 8.0, 10.0, 10.0]


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, None),
        ("120", 120.0),
        (" 5 ", 5.0),
        ("Tue, 17 Nov 2026 10:01:00 GMT", 60.0),
        ("Tue, 17 Nov 2026 09:00:00 GMT", 0.0),  # date in the past: no wait
        ("soon", None),
        ("²", None),  # a digit for str.isdigit, but not a number for float()
    ],
)
def test_parse_retry_after(header, expected):
    now = datetime(2026, 11, 17, 10, 0, 0, tzinfo=UTC)

    assert parse_retry_after(header, now=now) == expected


def test_retries_timeout(mocked, waits, tmp_path):
    mocked.get(URL, body=requests.Timeout("read timed out"))
    mocked.get(URL, body=BODY)

    result = fetch(tmp_path / "book.txt", waits)

    assert result.downloaded is True
    assert waits == [2.0]


def test_unparseable_retry_after_falls_back_to_backoff(mocked, waits, tmp_path):
    mocked.get(URL, status=503, headers={"Retry-After": "later"})
    mocked.get(URL, body=BODY)

    fetch(tmp_path / "book.txt", waits)

    assert waits == [2.0]


def test_gzip_transfer_is_decompressed_and_not_size_checked(mocked, waits, tmp_path):
    # Content-Length is the compressed size: comparing it with the decompressed bytes
    # written to disk would wrongly report an incomplete body.
    compressed = gzip.compress(BODY)
    mocked.get(
        URL,
        body=compressed,
        headers={"Content-Encoding": "gzip", "Content-Length": str(len(compressed))},
    )

    result = fetch(tmp_path / "book.txt", waits)

    assert (tmp_path / "book.txt").read_bytes() == BODY
    assert result.size_bytes == len(BODY)
    assert waits == []


def test_interrupt_halfway_through_body_removes_part_file(mocked, waits, tmp_path, monkeypatch):
    # Simulate Ctrl+C after the first chunk has been written to the .part file.
    class InterruptingHash:
        def update(self, chunk: bytes) -> None:
            assert (tmp_path / "book.txt.part").stat().st_size > 0
            raise KeyboardInterrupt

    monkeypatch.setattr(download.hashlib, "sha256", InterruptingHash)
    mocked.get(URL, body=BODY)

    with pytest.raises(KeyboardInterrupt):
        fetch(tmp_path / "book.txt", waits)

    assert names(tmp_path) == ["book.txt.lock"]
    assert waits == []


def test_waits_for_concurrent_download_and_then_skips(mocked, waits, tmp_path):
    # Another process is downloading the same file: it holds the lock.
    dest = tmp_path / "book.txt"
    lock = (tmp_path / "book.txt.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX)
    results = []
    worker = threading.Thread(target=lambda: results.append(fetch(dest, waits)))

    worker.start()
    worker.join(timeout=0.5)
    assert worker.is_alive()  # blocked on the lock, not downloading

    # The other process finishes its download and releases the lock.
    dest.write_bytes(BODY)
    lock.close()
    worker.join(timeout=5)

    assert not worker.is_alive()
    assert results[0].downloaded is False
    assert results[0].sha256 == hashlib.sha256(BODY).hexdigest()
    assert len(mocked.calls) == 0  # no second request to the source


def test_existing_file_is_skipped_without_creating_lock(mocked, waits, tmp_path):
    (tmp_path / "book.txt").write_bytes(BODY)

    fetch(tmp_path / "book.txt", waits)

    assert names(tmp_path) == ["book.txt"]
