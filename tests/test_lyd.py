import json
import shutil
import subprocess

import pytest

from fransk import lyd

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="krever ffmpeg")


def tone(sti, sekunder):
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={sekunder}", str(sti)],
        check=True,
    )
    return sti


def test_sett_sammen_lengde_og_tagger(tmp_path):
    a = tone(tmp_path / "a.mp3", 1)
    b = tone(tmp_path / "b.aiff", 1)
    ut = tmp_path / "ut" / "uke-03.mp3"
    lyd.sett_sammen([a, 2.0, b], ut, "Uke 03: Test", 3)
    assert lyd.varighet(ut) == 4
    info = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format_tags:stream=channels,sample_rate", "-of", "json", str(ut)],
        check=True, capture_output=True, text=True,
    ).stdout)
    tagger = info["format"]["tags"]
    assert tagger["title"] == "Uke 03: Test"
    assert tagger["album"] == "Fransk på løpetur"
    assert tagger["track"] == "3"
    assert info["streams"][0]["channels"] == 1
    assert info["streams"][0]["sample_rate"] == "44100"


def test_mangler_ffmpeg(monkeypatch):
    monkeypatch.setattr(lyd.shutil, "which", lambda navn: None)
    with pytest.raises(lyd.LydFeil, match="brew install ffmpeg"):
        lyd.krev_ffmpeg()


def test_avbrutt_koding_etterlater_ingen_fil(tmp_path, monkeypatch):
    a = tone(tmp_path / "a.mp3", 1)
    ekte = lyd._ffmpeg

    def avbryt_siste(*args):
        if "concat" in args:
            open(args[-1], "wb").write(b"halv")
            raise lyd.LydFeil("ffmpeg feilet: avbrutt")
        ekte(*args)

    monkeypatch.setattr(lyd, "_ffmpeg", avbryt_siste)
    ut = tmp_path / "uke-01.mp3"
    with pytest.raises(lyd.LydFeil):
        lyd.sett_sammen([a], ut, "T", 1)
    assert not ut.exists()
    assert list(tmp_path.glob("*.tmp.mp3")) == []


def test_odelagt_mp3_gir_lydfeil(tmp_path):
    ut = tmp_path / "uke-01.mp3"
    ut.write_bytes(b"ikke lyd")
    with pytest.raises(lyd.LydFeil, match="kjør fransk lag"):
        lyd.varighet(ut)
