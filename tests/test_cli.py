import subprocess
from pathlib import Path

import pytest

from conftest import gyldig_data, skriv_manus
from fransk import cli


def git(rot, *args):
    return subprocess.run(["git", *args], cwd=rot, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path, monkeypatch):
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    rot = tmp_path / "repo"
    rot.mkdir()
    git(rot, "init", "-q", "-b", "main")
    git(rot, "config", "user.email", "t@t")
    git(rot, "config", "user.name", "t")
    git(rot, "config", "commit.gpgsign", "false")
    git(rot, "remote", "add", "origin", str(remote))
    (rot / "README.md").write_text("x")
    git(rot, "add", ".")
    git(rot, "commit", "-q", "-m", "start")
    git(rot, "push", "-q", "-u", "origin", "main")
    monkeypatch.chdir(rot)

    def fake_bygg(ep, ut, cache_dir):
        ut.parent.mkdir(parents=True, exist_ok=True)
        ut.write_bytes(b"mp3")

    monkeypatch.setattr(cli, "bygg_episode", fake_bygg)
    monkeypatch.setattr(cli.lyd, "varighet", lambda p: 1300)
    return rot


def test_sjekk_gyldig(repo, capsys):
    skriv_manus(repo / "episoder", gyldig_data(1))
    assert cli.main(["sjekk", "1"]) == 0
    assert "gyldig" in capsys.readouterr().out


def test_lag_uten_manus_gir_norsk_feil(repo, capsys):
    assert cli.main(["lag", "4"]) == 1
    assert "Feil: Finner ikke manus" in capsys.readouterr().err


def test_repetisjon_skriver_gloser(repo, capsys):
    skriv_manus(repo / "episoder", gyldig_data(1))
    assert cli.main(["repetisjon", "2"]) == 0
    ut = capsys.readouterr().out
    assert "mot1-0 – ord1-0 (uke 1)" in ut


def test_repetisjon_uke_1(repo, capsys):
    assert cli.main(["repetisjon", "1"]) == 0
    assert "Ingen tidligere gloser" in capsys.readouterr().out


def test_publiser_committer_og_pusher(repo):
    skriv_manus(repo / "episoder", gyldig_data(1))
    assert cli.main(["publiser", "1"]) == 0
    assert (repo / "docs" / "feed.xml").exists()
    assert "Publiser uke 01" in git(repo, "log", "origin/main", "--oneline")
    assert git(repo, "status", "--porcelain") == ""


def test_publiser_to_ganger_krasjer_ikke(repo, capsys):
    skriv_manus(repo / "episoder", gyldig_data(1))
    assert cli.main(["publiser", "1"]) == 0
    assert cli.main(["publiser", "1"]) == 0
    assert "Ingenting nytt" in capsys.readouterr().out


def test_publiser_stopper_ved_andre_endringer(repo, capsys):
    skriv_manus(repo / "episoder", gyldig_data(1))
    (repo / "README.md").write_text("endret")
    assert cli.main(["publiser", "1"]) == 1
    assert "README.md" in capsys.readouterr().err


def test_git_endringer_finner_utsporede_filer(repo):
    (repo / "docs").mkdir()
    (repo / "docs" / "a.txt").write_text("a")
    assert cli.git_endringer(repo) == ["docs/a.txt"]
