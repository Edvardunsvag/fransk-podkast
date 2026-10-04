import xml.etree.ElementTree as ET

from conftest import gyldig_data
from fransk.feed import beskrivelse, lag_feed, publiseringstid
from fransk.manus import _valider

ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"


def ep(uke, **endringer):
    data = gyldig_data(uke)
    data.update(endringer)
    return _valider(data, f"uke-{uke:02d}.yaml")


def test_feed_med_to_episoder_og_en_uten_lyd(tmp_path):
    (tmp_path / "uke-01.mp3").write_bytes(b"x" * 100)
    (tmp_path / "uke-02.mp3").write_bytes(b"x" * 200)
    xml = lag_feed([ep(1), ep(2), ep(3)], tmp_path, "https://eks.no/p", varighet=lambda p: 1300)
    rot = ET.fromstring(xml)
    items = rot.findall("channel/item")
    assert [i.findtext(f"{ITUNES}episode") for i in items] == ["2", "1"]
    enc = items[0].find("enclosure")
    assert enc.get("url") == "https://eks.no/p/lyd/uke-02.mp3"
    assert enc.get("length") == "200"
    assert enc.get("type") == "audio/mpeg"
    assert items[0].findtext(f"{ITUNES}duration") == "1300"
    assert rot.find(f"channel/{ITUNES}image").get("href") == "https://eks.no/p/cover.jpg"


def test_spesialtegn_escapes(tmp_path):
    (tmp_path / "uke-01.mp3").write_bytes(b"x")
    e = ep(1, codex_instruks='Si "bonjour" & <smil>', tittel="Kafé & croissant")
    xml = lag_feed([e], tmp_path, "https://eks.no/p", varighet=lambda p: 1)
    item = ET.fromstring(xml).find("channel/item")
    assert item.findtext("title") == "Uke 01: Kafé & croissant"
    assert 'Si "bonjour" & <smil>' in item.findtext("description")


def test_beskrivelse_har_gloser_fraser_og_instruks():
    tekst = beskrivelse(ep(1))
    assert "mot1-0: ord1-0" in tekst
    assert "phrase 0: frase 0" in tekst
    assert "Du er en fransk turist." in tekst


def test_publiseringstid_er_ukentlig():
    assert (publiseringstid(2) - publiseringstid(1)).days == 7
    assert publiseringstid(1).hour == 6
