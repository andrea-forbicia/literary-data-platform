import gzip
import logging
from datetime import date

import pytest
import requests
import responses

from literary_data_platform.ingestion.gutenberg import (
    catalog_path,
    catalog_url,
    download_catalog,
    main,
)

MIRROR = "https://mirror.example.org"
URL = f"{MIRROR}/cache/epub/feeds/pg_catalog.csv.gz"
# Two real-looking rows, one with a line break inside a quoted title.
CSV = (
    "Text#,Type,Issued,Title,Language,Authors,Subjects,LoCC,Bookshelves\n"
    '2,Text,1972-12-01,"The United States Bill of Rights\nThe Ten Original Amendments",'
    "en,United States,Civil rights,JK; KF,Politics\n"
)
BODY = gzip.compress(CSV.encode())
SNAPSHOT = date(2026, 11, 27)


@pytest.fixture
def mocked():
    with responses.RequestsMock() as rsps:
        yield rsps


def env(tmp_path) -> dict[str, str]:
    return {
        "DATA_DIR": str(tmp_path),
        "GUTENBERG_MIRROR_URL": MIRROR,
        "HTTP_USER_AGENT": "literary-data-platform/test",
    }


@pytest.mark.parametrize("mirror", [MIRROR, MIRROR + "/"])
def test_catalog_url_with_or_without_trailing_slash(mirror):
    assert catalog_url(mirror) == URL


def test_catalog_path_is_partitioned_by_source_and_date(tmp_path):
    assert catalog_path(tmp_path, SNAPSHOT) == (
        tmp_path / "raw" / "gutenberg" / "2026-11-27" / "pg_catalog.csv.gz"
    )


def test_catalogue_is_stored_as_it_arrives(mocked, tmp_path):
    mocked.get(URL, body=BODY)

    with requests.Session() as session:
        result = download_catalog(session, MIRROR, tmp_path, SNAPSHOT)

    # Still compressed and byte for byte identical: the raw layer does not transform.
    assert result.path.read_bytes() == BODY
    assert gzip.decompress(result.path.read_bytes()).decode() == CSV


def test_same_date_is_skipped_and_new_date_downloads_again(mocked, tmp_path):
    mocked.get(URL, body=BODY)
    with requests.Session() as session:
        download_catalog(session, MIRROR, tmp_path, SNAPSHOT)
        again = download_catalog(session, MIRROR, tmp_path, SNAPSHOT)
        next_week = download_catalog(session, MIRROR, tmp_path, date(2026, 12, 4))

    assert again.downloaded is False
    assert next_week.downloaded is True
    assert len(mocked.calls) == 2  # one request per snapshot date
    assert next_week.sha256 == again.sha256  # unchanged catalogue: identical copies (D12)


def test_main_downloads_with_date_and_user_agent(mocked, tmp_path):
    mocked.get(URL, body=BODY)

    exit_code = main(["--date", "2026-11-27"], env(tmp_path))

    assert exit_code == 0
    assert catalog_path(tmp_path, SNAPSHOT).read_bytes() == BODY
    assert mocked.calls[0].request.headers["User-Agent"] == "literary-data-platform/test"


def test_main_fails_cleanly_when_a_setting_is_missing(mocked, tmp_path, caplog):
    settings = env(tmp_path)
    del settings["GUTENBERG_MIRROR_URL"]

    with caplog.at_level(logging.ERROR):
        exit_code = main(["--date", "2026-11-27"], settings)

    assert exit_code == 1
    assert "GUTENBERG_MIRROR_URL" in caplog.text
    assert len(mocked.calls) == 0


def test_main_fails_cleanly_when_the_source_is_unavailable(mocked, tmp_path, caplog):
    # The main site's answer during maintenance: retrying would mean waiting 6 hours.
    mocked.get(URL, status=503, headers={"Retry-After": "21600"})

    with caplog.at_level(logging.ERROR):
        exit_code = main(["--date", "2026-11-27"], env(tmp_path))

    assert exit_code == 1
    assert "21600" in caplog.text
    assert not catalog_path(tmp_path, SNAPSHOT).exists()


def test_main_rejects_an_invalid_date(tmp_path):
    with pytest.raises(SystemExit) as excinfo:
        main(["--date", "27/11/2026"], env(tmp_path))

    assert excinfo.value.code == 2  # argparse usage error
