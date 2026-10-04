from pathlib import Path

from conftest import gyldig_data
from fransk import bygg
from fransk.manus import _valider


def test_bygg_setter_inn_mellomrom_og_pauser(tmp_path, monkeypatch):
    laget = []

    def fake_lag_lyd(tekst, sprak, fart, stemme, cache_dir):
        laget.append((tekst, sprak, fart, stemme))
        return Path(f"/fake/{len(laget)}.mp3")

    fanget = {}

    def fake_sett_sammen(deler, ut, tittel, uke):
        fanget.update(deler=deler, ut=ut, tittel=tittel, uke=uke)

    monkeypatch.setattr(bygg.tale, "lag_lyd", fake_lag_lyd)
    monkeypatch.setattr(bygg.lyd, "sett_sammen", fake_sett_sammen)

    ep = _valider(gyldig_data(1), "uke-01.yaml")
    bygg.bygg_episode(ep, tmp_path / "uke-01.mp3", tmp_path)

    assert laget[1] == ("Bonjour", "fr", "sakte", "a")
    assert laget[2] == ("Vous venez d'où ?", "fr", "normal", "b")
    assert fanget["deler"] == [
        Path("/fake/1.mp3"), 0.4, Path("/fake/2.mp3"), 3.0, Path("/fake/3.mp3"),
    ]
    assert fanget["tittel"] == "Uke 01: Hei, hvor kommer du fra?"
    assert fanget["uke"] == 1
