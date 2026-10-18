import pytest

from fransk import tale


@pytest.fixture(autouse=True)
def nullstill(monkeypatch):
    monkeypatch.setattr(tale, "_edge_av", False)


@pytest.fixture
def azure_feiler(monkeypatch):
    def feiler(*args):
        raise RuntimeError("azure nede")

    monkeypatch.setattr(tale, "_azure", feiler)


def skriv(innhold=b"lyd"):
    kall = []

    def motor(tekst, stemme_navn, fart, ut):
        kall.append((tekst, stemme_navn, fart))
        ut.write_bytes(innhold)

    return motor, kall


def test_bruker_edge_med_riktig_stemme(tmp_path, monkeypatch):
    edge, kall = skriv()
    monkeypatch.setattr(tale, "_edge", edge)
    sti = tale.lag_lyd("Bonjour", "fr", "sakte", "b", tmp_path)
    assert sti.suffix == ".mp3"
    assert kall == [("Bonjour", "fr-FR-HenriNeural", "-20%")]


def test_mellomlagring(tmp_path, monkeypatch):
    edge, kall = skriv()
    monkeypatch.setattr(tale, "_edge", edge)
    a = tale.lag_lyd("Hei", "no", cache_dir=tmp_path)
    b = tale.lag_lyd("Hei", "no", cache_dir=tmp_path)
    assert a == b
    assert len(kall) == 1


def test_bytter_til_say_naar_edge_feiler(tmp_path, monkeypatch, capsys, azure_feiler):
    def feiler(*args):
        raise RuntimeError("nett nede")

    say, kall = skriv()
    monkeypatch.setattr(tale, "_edge", feiler)
    monkeypatch.setattr(tale, "_say", say)
    sti = tale.lag_lyd("Vous venez d'où ?", "fr", "normal", "a", tmp_path)
    tale.lag_lyd("Merci", "fr", cache_dir=tmp_path)
    assert sti.suffix == ".aiff"
    assert kall[0] == ("Vous venez d'où ?", "Thomas", "185")
    assert capsys.readouterr().err.count("edge-tts feilet") == 1


def test_tom_edge_fil_regnes_som_feil(tmp_path, monkeypatch, azure_feiler):
    edge, _ = skriv(b"")
    say, kall = skriv()
    monkeypatch.setattr(tale, "_edge", edge)
    monkeypatch.setattr(tale, "_say", say)
    sti = tale.lag_lyd("Salut", "fr", cache_dir=tmp_path)
    assert sti.suffix == ".aiff" and len(kall) == 1


def test_alle_feiler(tmp_path, monkeypatch, azure_feiler):
    def feiler(*args):
        raise RuntimeError("borte")

    monkeypatch.setattr(tale, "_edge", feiler)
    monkeypatch.setattr(tale, "_say", feiler)
    with pytest.raises(tale.TaleFeil, match="«Salut»"):
        tale.lag_lyd("Salut", "fr", cache_dir=tmp_path)


def test_bytter_til_azure_naar_edge_feiler(tmp_path, monkeypatch, capsys):
    def feiler(*args):
        raise RuntimeError("403")

    azure_kall = []

    def azure(tekst, sprak, stemme_navn, fart, ut):
        azure_kall.append((tekst, sprak, stemme_navn, fart))
        ut.write_bytes(b"lyd")

    monkeypatch.setattr(tale, "_edge", feiler)
    monkeypatch.setattr(tale, "_azure", azure)
    sti = tale.lag_lyd("Bonjour", "fr", "sakte", "b", tmp_path)
    tale.lag_lyd("Merci", "fr", cache_dir=tmp_path)
    assert sti.suffix == ".mp3"
    assert azure_kall[0] == ("Bonjour", "fr", "fr-FR-HenriNeural", "-20%")
    assert capsys.readouterr().err.count("edge-tts feilet") == 1


@pytest.mark.skipif(not __import__("shutil").which("say"), reason="krever macOS say")
def test_say_ekte_med_vanskelig_tekst(tmp_path):
    ut = tmp_path / "x.aiff"
    tale._say("-là, d'où « ça » ?", "Thomas", "150", ut)
    assert ut.stat().st_size > 1000
