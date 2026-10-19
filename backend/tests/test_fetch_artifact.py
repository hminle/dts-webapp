import urllib.request
from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest

from app.core.config import get_settings
from scripts import fetch_artifact


@pytest.fixture
def dest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    path = tmp_path / "data" / "treasury_data.duckdb"
    monkeypatch.setenv("APP_DUCKDB_PATH", str(path))
    get_settings.cache_clear()
    yield path
    get_settings.cache_clear()


def _use_url(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    monkeypatch.setenv("APP_ARTIFACT_URL", url)
    get_settings.cache_clear()


def test_skips_when_url_unset(dest: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_ARTIFACT_URL", raising=False)

    assert fetch_artifact.main() == 0
    assert not dest.exists()


def test_rejects_a_file_that_is_not_an_artifact(
    dest: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    junk = tmp_path / "junk.bin"
    junk.write_bytes(b"not a database")
    _use_url(monkeypatch, junk.as_uri())

    assert fetch_artifact.main() == 1
    assert not dest.exists()
    assert not dest.with_suffix(".download").exists()


def test_installs_a_valid_artifact(
    dest: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "source.duckdb"
    conn = duckdb.connect(str(source))
    conn.execute("CREATE TABLE metadata (key VARCHAR PRIMARY KEY, value VARCHAR)")
    conn.execute("INSERT INTO metadata VALUES ('latest_record_date', '2026-10-16')")
    conn.close()
    _use_url(monkeypatch, source.as_uri())

    assert fetch_artifact.main() == 0
    assert dest.exists()


def test_sends_a_named_user_agent(
    dest: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen: list[str | None] = []
    real_urlopen = fetch_artifact.urllib.request.urlopen

    def spy(request: urllib.request.Request, timeout: float):
        seen.append(request.get_header("User-agent"))
        return real_urlopen(request, timeout=timeout)

    junk = tmp_path / "junk.bin"
    junk.write_bytes(b"x")
    _use_url(monkeypatch, junk.as_uri())
    monkeypatch.setattr(fetch_artifact.urllib.request, "urlopen", spy)

    fetch_artifact.main()

    assert seen == [fetch_artifact.USER_AGENT]
