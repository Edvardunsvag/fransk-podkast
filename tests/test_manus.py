import pytest

from conftest import gyldig_data, skriv_manus
from fransk.manus import ManusFeil, Ord, Segment, les_alle, les_episode, manus_sti


def test_gyldig_manus(tmp_path):
    sti = skriv_manus(tmp_path, gyldig_data(1))
    ep = les_episode(sti)
    assert ep.uke == 1
    assert len(ep.gloser) == 10
    assert ep.gloser[0] == Ord(fr="mot1-0", no="ord1-0")
    assert ep.segmenter[0] == Segment(type="no", tekst="Velkommen til uke én.")
    assert ep.segmenter[1] == Segment(type="fr", tekst="Bonjour", fart="sakte", stemme="a")
    assert ep.segmenter[2] == Segment(type="pause", sekunder=3.0)
    assert ep.segmenter[3] == Segment(type="fr", tekst="Vous venez d'où ?", fart="normal", stemme="b")


def test_manus_sti(tmp_path):
    assert manus_sti(tmp_path, 3) == tmp_path / "uke-03.yaml"


def test_manglende_fil(tmp_path):
    with pytest.raises(ManusFeil, match="Finner ikke manus"):
        les_episode(tmp_path / "uke-01.yaml")


def test_ugyldig_yaml(tmp_path):
    sti = tmp_path / "uke-01.yaml"
    sti.write_text("uke: [1", encoding="utf-8")
    with pytest.raises(ManusFeil, match="ugyldig YAML"):
        les_episode(sti)


def _feil(tmp_path, endring, melding):
    data = gyldig_data(1)
    endring(data)
    sti = tmp_path / "uke-01.yaml"
    import yaml
    sti.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ManusFeil, match=melding):
        les_episode(sti)


def test_manglende_felt(tmp_path):
    _feil(tmp_path, lambda d: d.pop("tittel"), "mangler felt: tittel")


def test_ukjent_felt(tmp_path):
    _feil(tmp_path, lambda d: d.update(forfatter="x"), "ukjente felt: forfatter")


def test_feil_uke_mot_filnavn(tmp_path):
    _feil(tmp_path, lambda d: d.update(uke=2), "stemmer ikke med filnavnet")


def test_tom_tittel(tmp_path):
    _feil(tmp_path, lambda d: d.update(tittel="  "), "tittel kan ikke være tom")


def test_ni_gloser(tmp_path):
    _feil(tmp_path, lambda d: d["gloser"].pop(), "nøyaktig 10")


def test_for_mange_fraser(tmp_path):
    _feil(tmp_path, lambda d: d["fraser"].extend([{"fr": "a", "no": "b"}] * 3), "mellom 6 og 8")


def test_glose_uten_norsk(tmp_path):
    _feil(tmp_path, lambda d: d["gloser"][0].pop("no"), "gloser nr. 1")


def test_tom_segmenttekst(tmp_path):
    _feil(tmp_path, lambda d: d["segmenter"].append({"fr": " "}), "segment 5: tom tekst")


def test_to_typer_i_segment(tmp_path):
    _feil(tmp_path, lambda d: d["segmenter"].append({"fr": "a", "no": "b"}), "nøyaktig én av no, fr og pause")


def test_pause_med_fart(tmp_path):
    _feil(tmp_path, lambda d: d["segmenter"].append({"pause": 2, "fart": "sakte"}), "pause kan ikke ha")


def test_negativ_pause(tmp_path):
    _feil(tmp_path, lambda d: d["segmenter"].append({"pause": 0}), "positivt tall")


def test_ugyldig_fart(tmp_path):
    _feil(tmp_path, lambda d: d["segmenter"].append({"fr": "a", "fart": "rask"}), "fart må være")


def test_stemme_paa_norsk(tmp_path):
    _feil(tmp_path, lambda d: d["segmenter"].append({"no": "a", "stemme": "b"}), "stemme gjelder bare fransk")


def test_tomme_segmenter(tmp_path):
    _feil(tmp_path, lambda d: d.update(segmenter=[]), "segmenter kan ikke være tom")


def test_les_alle_sortert(tmp_path):
    skriv_manus(tmp_path, gyldig_data(2))
    skriv_manus(tmp_path, gyldig_data(1))
    assert [e.uke for e in les_alle(tmp_path)] == [1, 2]


def test_ukvotert_no_er_en_vanlig_nokkel(tmp_path):
    gloser = "\n".join(f'  - {{ fr: "mot{i}", no: "ord{i}" }}' for i in range(10))
    fraser = "\n".join(f'  - {{ fr: "phrase {i}", no: "frase {i}" }}' for i in range(6))
    sti = tmp_path / "uke-01.yaml"
    sti.write_text(
        f"""uke: 1
tittel: "T"
beskrivelse: "B"
gloser:
{gloser}
fraser:
{fraser}
codex_instruks: "C"
segmenter:
  - no: "Hei"
  - fr: "Bonjour"
""",
        encoding="utf-8",
    )
    ep = les_episode(sti)
    assert ep.gloser[0] == Ord(fr="mot0", no="ord0")
    assert ep.segmenter[0] == Segment(type="no", tekst="Hei")


def test_andre_ord_er_valgfritt(tmp_path):
    assert les_episode(skriv_manus(tmp_path, gyldig_data(1))).andre_ord == []


def test_andre_ord_leses(tmp_path):
    data = gyldig_data(1)
    data["andre_ord"] = [{"fr": "venir", "no": "å komme"}]
    assert les_episode(skriv_manus(tmp_path, data)).andre_ord == [Ord("venir", "å komme")]


def test_andre_ord_valideres(tmp_path):
    _feil(tmp_path, lambda d: d.update(andre_ord=[{"fr": "venir"}]), "andre_ord nr. 1")
