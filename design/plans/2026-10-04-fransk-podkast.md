# Fransk-podkast Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Et Python-verktøy som gjør ukentlige YAML-manus om til franskleksjoner i MP3 og publiserer dem som en podkastfeed på GitHub Pages.

**Architecture:** En liten Python-pakke `fransk` med én modul per oppgave: `manus` (lese og validere), `repetisjon` (velge gamle gloser), `tale` (edge-tts med macOS `say` som reserve, mellomlagret), `lyd` (ffmpeg-sammensetting), `bygg` (manus til MP3), `feed` (RSS) og `cli`. Repoets rot er arbeidsmappa; manus ligger i `episoder/`, alt som publiseres ligger i `docs/`.

**Tech Stack:** Python 3.12+, uv, edge-tts, PyYAML, ffmpeg/ffprobe, macOS `say`, pytest, GitHub Pages.

**Spec:** `design/specs/2026-10-04-fransk-podkast-design.md`

## Global Constraints

- All kode kjøres fra repoets rot med `uv run`. Stier regnes fra `Path.cwd()`.
- Ingen betalte tjenester. Avhengigheter: `edge-tts`, `pyyaml`, og `pytest` som dev-avhengighet. Ikke noe annet.
- Stemmer, edge-tts: norsk `nb-NO-FinnNeural`, fransk a `fr-FR-DeniseNeural`, fransk b `fr-FR-HenriNeural`. Sakte fart `-20%`, normal `+0%`.
- Stemmer, `say`: norsk `Nora`, fransk a `Thomas`, fransk b `Jacques`.
- MP3: mono, 64 kbit/s, 44,1 kHz, `loudnorm`. ID3: tittel `Uke NN: <tittel>`, album `Fransk på løpetur`, spor = uke.
- Manus: nøyaktig 10 gloser, 6–8 fraser, `uke` lik tallet i filnavnet `uke-NN.yaml`.
- Repetisjon: uke N−1, N−2, N−4, N−8, til sammen maks 8 gloser.
- Feed-URL: `https://edvardunsvag.github.io/fransk-podkast/feed.xml`. GitHub-bruker `Edvardunsvag`, repo `fransk-podkast`, offentlig, Pages fra `main` `/docs`.
- Feilmeldinger og CLI-utskrift er på norsk. Identifikatorer i koden er ASCII (`sprak`, ikke `språk`).
- `.cache/` og `.venv/` er gitignored.

## Review Focus

1. Fransk tekst med apostrof, bindestrek først, guillemets og ikke-ASCII (`d'où`, `-là`, `ç`, `«`) må gi riktig lyd i både edge-tts og `say`. `say` får teksten fra fil, aldri som argument. Testet i Task 3.
2. edge-tts som «lykkes» men lager en tom fil skal behandles som feil og gi bytte til `say`. Testet i Task 3.
3. `fransk lag N` når `episoder/uke-NN.yaml` ikke finnes skal gi en norsk feilmelding og exit-kode 1, ikke en traceback. Testet i Task 6.
4. `codex_instruks` og gloser med `&`, `<` og `"` skal escapes riktig i feeden, og et manus uten MP3 skal ikke havne i feeden. Testet i Task 5.
5. `fransk publiser N` når ingenting har endret seg skal ikke krasje på tom commit. Testet i Task 6.

---

### Task 1: Prosjektoppsett og manus

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `src/fransk/__init__.py`, `src/fransk/config.py`, `src/fransk/manus.py`
- Test: `tests/conftest.py`, `tests/test_manus.py`

**Interfaces:**
- Consumes: ingenting
- Produces:
  - `fransk.config`: `BASE_URL: str`, `START_DATO: date`, `PODKAST_TITTEL: str`, `PODKAST_BESKRIVELSE: str`, `FORFATTER: str`
  - `fransk.manus`: `class ManusFeil(Exception)`, `@dataclass(frozen=True) Ord(fr: str, no: str)`, `Segment(type: str, tekst: str = "", fart: str = "sakte", stemme: str = "a", sekunder: float = 0.0)` der `type` er `"no" | "fr" | "pause"`, `Episode(uke: int, tittel: str, beskrivelse: str, gloser: list[Ord], fraser: list[Ord], codex_instruks: str, segmenter: list[Segment])`, `manus_sti(mappe: Path, uke: int) -> Path`, `les_episode(sti: Path) -> Episode`, `les_alle(mappe: Path) -> list[Episode]`
  - `tests/conftest.py`: `gyldig_data(uke: int = 1) -> dict`, `skriv_manus(mappe: Path, data: dict) -> Path`

- [ ] **Step 1: Lag prosjektfilene**

`pyproject.toml`:

```toml
[project]
name = "fransk"
version = "0.1.0"
description = "Franskleksjoner som podkast for rolige løpeturer"
requires-python = ">=3.12"
dependencies = ["edge-tts>=7.0", "pyyaml>=6.0"]

[project.scripts]
fransk = "fransk.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = ["pytest>=8"]

[tool.pytest.ini_options]
pythonpath = ["tests"]
```

`.gitignore`:

```
.venv/
.cache/
__pycache__/
*.pyc
.pytest_cache/
```

`src/fransk/__init__.py`: tom fil.

`src/fransk/config.py`:

```python
from datetime import date

BASE_URL = "https://edvardunsvag.github.io/fransk-podkast"
START_DATO = date(2026, 10, 4)
PODKAST_TITTEL = "Fransk på løpetur"
PODKAST_BESKRIVELSE = "Én fransk leksjon i uka, laget for rolige løpeturer."
FORFATTER = "Edvard"
```

`src/fransk/manus.py` (bare stub så testene kan importere):

```python
class ManusFeil(Exception):
    pass
```

Kjør: `uv sync`
Forventet: oppretter `.venv` og `uv.lock` uten feil.

- [ ] **Step 2: Skriv testhjelpere**

`tests/conftest.py`:

```python
from pathlib import Path

import yaml


def gyldig_data(uke: int = 1) -> dict:
    return {
        "uke": uke,
        "tittel": "Hei, hvor kommer du fra?",
        "beskrivelse": "Hilse og spørre hvor folk kommer fra.",
        "gloser": [{"fr": f"mot{uke}-{i}", "no": f"ord{uke}-{i}"} for i in range(10)],
        "fraser": [{"fr": f"phrase {i}", "no": f"frase {i}"} for i in range(6)],
        "codex_instruks": "Du er en fransk turist.",
        "segmenter": [
            {"no": "Velkommen til uke én."},
            {"fr": "Bonjour", "fart": "sakte"},
            {"pause": 3},
            {"fr": "Vous venez d'où ?", "stemme": "b", "fart": "normal"},
        ],
    }


def skriv_manus(mappe: Path, data: dict) -> Path:
    mappe.mkdir(parents=True, exist_ok=True)
    sti = mappe / f"uke-{data['uke']:02d}.yaml"
    sti.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return sti
```

- [ ] **Step 3: Skriv feilende tester**

`tests/test_manus.py`:

```python
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
```

- [ ] **Step 4: Kjør testene og se at de feiler**

Kjør: `uv run pytest tests/test_manus.py -q`
Forventet: FAIL med `ImportError: cannot import name 'Ord'`.

- [ ] **Step 5: Implementer `manus.py`**

```python
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

TOPP_FELT = {"uke", "tittel", "beskrivelse", "gloser", "fraser", "codex_instruks", "segmenter"}
SEGMENT_FELT = {"no", "fr", "pause", "fart", "stemme"}


class ManusFeil(Exception):
    pass


@dataclass(frozen=True)
class Ord:
    fr: str
    no: str


@dataclass(frozen=True)
class Segment:
    type: str
    tekst: str = ""
    fart: str = "sakte"
    stemme: str = "a"
    sekunder: float = 0.0


@dataclass(frozen=True)
class Episode:
    uke: int
    tittel: str
    beskrivelse: str
    gloser: list[Ord]
    fraser: list[Ord]
    codex_instruks: str
    segmenter: list[Segment]


def manus_sti(mappe: Path, uke: int) -> Path:
    return mappe / f"uke-{uke:02d}.yaml"


def les_episode(sti: Path) -> Episode:
    if not sti.exists():
        raise ManusFeil(f"Finner ikke manus: {sti}")
    try:
        data = yaml.safe_load(sti.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ManusFeil(f"{sti.name}: ugyldig YAML: {e}") from e
    return _valider(data, sti.name)


def les_alle(mappe: Path) -> list[Episode]:
    episoder = [les_episode(sti) for sti in mappe.glob("uke-*.yaml")]
    return sorted(episoder, key=lambda e: e.uke)


def _valider(data, navn: str) -> Episode:
    def feil(melding: str):
        raise ManusFeil(f"{navn}: {melding}")

    if not isinstance(data, dict):
        feil("manuset må være et YAML-objekt")
    mangler = TOPP_FELT - data.keys()
    if mangler:
        feil(f"mangler felt: {', '.join(sorted(mangler))}")
    ukjente = data.keys() - TOPP_FELT
    if ukjente:
        feil(f"ukjente felt: {', '.join(sorted(ukjente))}")

    treff = re.fullmatch(r"uke-(\d+)\.yaml", navn)
    if not isinstance(data["uke"], int) or not treff or int(treff.group(1)) != data["uke"]:
        feil(f"uke {data['uke']!r} stemmer ikke med filnavnet")

    for felt in ("tittel", "beskrivelse", "codex_instruks"):
        if not isinstance(data[felt], str) or not data[felt].strip():
            feil(f"{felt} kan ikke være tom")

    gloser = _ordliste(data["gloser"], "gloser", feil)
    if len(gloser) != 10:
        feil(f"gloser må ha nøyaktig 10 ord, har {len(gloser)}")
    fraser = _ordliste(data["fraser"], "fraser", feil)
    if not 6 <= len(fraser) <= 8:
        feil(f"fraser må ha mellom 6 og 8, har {len(fraser)}")

    if not isinstance(data["segmenter"], list) or not data["segmenter"]:
        feil("segmenter kan ikke være tom")
    segmenter = [_segment(s, nr, feil) for nr, s in enumerate(data["segmenter"], 1)]

    return Episode(
        uke=data["uke"],
        tittel=data["tittel"].strip(),
        beskrivelse=data["beskrivelse"].strip(),
        gloser=gloser,
        fraser=fraser,
        codex_instruks=data["codex_instruks"].strip(),
        segmenter=segmenter,
    )


def _ordliste(verdi, felt: str, feil) -> list[Ord]:
    if not isinstance(verdi, list):
        feil(f"{felt} må være en liste")
    ord_ = []
    for nr, o in enumerate(verdi, 1):
        if (
            not isinstance(o, dict)
            or o.keys() != {"fr", "no"}
            or not all(isinstance(o[k], str) and o[k].strip() for k in ("fr", "no"))
        ):
            feil(f"{felt} nr. {nr} må ha fr og no med tekst")
        ord_.append(Ord(fr=o["fr"].strip(), no=o["no"].strip()))
    return ord_


def _segment(s, nr: int, feil) -> Segment:
    if not isinstance(s, dict):
        feil(f"segment {nr}: må være et objekt")
    ukjente = s.keys() - SEGMENT_FELT
    if ukjente:
        feil(f"segment {nr}: ukjente felt: {', '.join(sorted(ukjente))}")
    typer = [t for t in ("no", "fr", "pause") if t in s]
    if len(typer) != 1:
        feil(f"segment {nr}: må ha nøyaktig én av no, fr og pause")
    type_ = typer[0]

    if type_ == "pause":
        if s.keys() != {"pause"}:
            feil(f"segment {nr}: pause kan ikke ha fart eller stemme")
        sek = s["pause"]
        if isinstance(sek, bool) or not isinstance(sek, (int, float)) or sek <= 0:
            feil(f"segment {nr}: pause må være et positivt tall")
        return Segment(type="pause", sekunder=float(sek))

    tekst = s[type_]
    if not isinstance(tekst, str) or not tekst.strip():
        feil(f"segment {nr}: tom tekst")
    fart = s.get("fart", "sakte")
    if fart not in ("sakte", "normal"):
        feil(f"segment {nr}: fart må være sakte eller normal")
    if type_ == "no" and "stemme" in s:
        feil(f"segment {nr}: stemme gjelder bare fransk")
    stemme = s.get("stemme", "a")
    if stemme not in ("a", "b"):
        feil(f"segment {nr}: stemme må være a eller b")
    return Segment(type=type_, tekst=tekst.strip(), fart=fart, stemme=stemme)
```

- [ ] **Step 6: Kjør testene**

Kjør: `uv run pytest tests/test_manus.py -q`
Forventet: alle PASS.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock .gitignore src tests
git commit -m "Legg til prosjektoppsett og manusvalidering"
```

---

### Task 2: Repetisjon

**Files:**
- Create: `src/fransk/repetisjon.py`
- Test: `tests/test_repetisjon.py`

**Interfaces:**
- Consumes: `fransk.manus.Episode`, `Ord`; `conftest.gyldig_data`
- Produces: `AVSTANDER = (1, 2, 4, 8)`, `MAKS = 8`, `velg_repetisjon(uke: int, episoder: list[Episode], maks: int = MAKS) -> list[tuple[int, Ord]]` (uke glosen kom fra, glosen)

Regel: kildene er ukene `uke − a` for `a` i `AVSTANDER` som finnes i `episoder`, i den rekkefølgen. Kilde nr. `j` (indeks i `AVSTANDER`, ikke i kildelista) starter på indeks `j * len(gloser) // len(AVSTANDER)` og går videre med omløp. Glosene hentes én om gangen fra hver kilde etter tur (rundgang) til `maks` er nådd eller kildene er tomme. Forskjøvet start gjør at en uke som repeteres fire ganger, viser ulike gloser hver gang.

- [ ] **Step 1: Skriv feilende tester**

```python
from conftest import gyldig_data
from fransk.manus import Episode, Ord, _valider
from fransk.repetisjon import velg_repetisjon


def ep(uke: int) -> Episode:
    return _valider(gyldig_data(uke), f"uke-{uke:02d}.yaml")


def test_uke_1_har_ingen_repetisjon():
    assert velg_repetisjon(1, [ep(1)]) == []


def test_uke_2_tar_8_fra_uke_1():
    valgt = velg_repetisjon(2, [ep(1), ep(2)])
    assert valgt == [(1, Ord(f"mot1-{i}", f"ord1-{i}")) for i in range(8)]


def test_uke_3_deler_jevnt_og_forskyver_start():
    valgt = velg_repetisjon(3, [ep(1), ep(2), ep(3)])
    assert len(valgt) == 8
    fra_uke_2 = [o.fr for u, o in valgt if u == 2]
    fra_uke_1 = [o.fr for u, o in valgt if u == 1]
    assert fra_uke_2 == ["mot2-0", "mot2-1", "mot2-2", "mot2-3"]
    assert fra_uke_1 == ["mot1-2", "mot1-3", "mot1-4", "mot1-5"]


def test_uke_9_bruker_1_2_4_8_uker_tilbake():
    episoder = [ep(u) for u in range(1, 10)]
    valgt = velg_repetisjon(9, episoder)
    assert sorted({u for u, _ in valgt}) == [1, 5, 7, 8]
    assert len(valgt) == 8
    assert [o.fr for u, o in valgt if u == 1] == ["mot1-7", "mot1-8"]


def test_manglende_uke_hoppes_over():
    valgt = velg_repetisjon(5, [ep(1), ep(4)])
    assert {u for u, _ in valgt} == {1, 4}
    assert len(valgt) == 8
```

- [ ] **Step 2: Kjør og se at de feiler**

Kjør: `uv run pytest tests/test_repetisjon.py -q`
Forventet: FAIL med `ModuleNotFoundError: No module named 'fransk.repetisjon'`.

- [ ] **Step 3: Implementer**

```python
from fransk.manus import Episode, Ord

AVSTANDER = (1, 2, 4, 8)
MAKS = 8


def velg_repetisjon(uke: int, episoder: list[Episode], maks: int = MAKS) -> list[tuple[int, Ord]]:
    per_uke = {e.uke: e.gloser for e in episoder}
    kilder = []
    for j, avstand in enumerate(AVSTANDER):
        kilde_uke = uke - avstand
        if kilde_uke in per_uke and per_uke[kilde_uke]:
            gloser = per_uke[kilde_uke]
            start = j * len(gloser) // len(AVSTANDER)
            kilder.append((kilde_uke, gloser, start))

    valgt: list[tuple[int, Ord]] = []
    runde = 0
    while len(valgt) < maks and any(runde < len(g) for _, g, _ in kilder):
        for kilde_uke, gloser, start in kilder:
            if runde < len(gloser) and len(valgt) < maks:
                valgt.append((kilde_uke, gloser[(start + runde) % len(gloser)]))
        runde += 1
    return valgt
```

Kontroll av `test_uke_9`: kilde uke 1 har `j = 3`, start `3 * 10 // 4 = 7`, gir `mot1-7`, `mot1-8`.

- [ ] **Step 4: Kjør testene**

Kjør: `uv run pytest tests/test_repetisjon.py -q`
Forventet: alle PASS.

- [ ] **Step 5: Commit**

```bash
git add src/fransk/repetisjon.py tests/test_repetisjon.py
git commit -m "Legg til valg av repetisjonsgloser"
```

---

### Task 3: Tale med edge-tts og say som reserve

**Files:**
- Create: `src/fransk/tale.py`
- Test: `tests/test_tale.py`

**Interfaces:**
- Consumes: ingenting fra tidligere tasks
- Produces: `class TaleFeil(Exception)`, `lag_lyd(tekst: str, sprak: str, fart: str = "sakte", stemme: str = "a", cache_dir: Path = Path(".cache")) -> Path`. `sprak` er `"no"` eller `"fr"`. Returnerer en ikke-tom lydfil (`.mp3` fra edge-tts eller `.aiff` fra `say`). Interne funksjoner som testene patcher: `_edge(tekst, stemme_navn, fart, ut)`, `_say(tekst, stemme_navn, fart, ut)`, modulvariabel `_edge_av: bool`.

- [ ] **Step 1: Skriv feilende tester**

```python
import pytest

from fransk import tale


@pytest.fixture(autouse=True)
def nullstill(monkeypatch):
    monkeypatch.setattr(tale, "_edge_av", False)


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


def test_bytter_til_say_naar_edge_feiler(tmp_path, monkeypatch, capsys):
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


def test_tom_edge_fil_regnes_som_feil(tmp_path, monkeypatch):
    edge, _ = skriv(b"")
    say, kall = skriv()
    monkeypatch.setattr(tale, "_edge", edge)
    monkeypatch.setattr(tale, "_say", say)
    sti = tale.lag_lyd("Salut", "fr", cache_dir=tmp_path)
    assert sti.suffix == ".aiff" and len(kall) == 1


def test_begge_feiler(tmp_path, monkeypatch):
    def feiler(*args):
        raise RuntimeError("borte")

    monkeypatch.setattr(tale, "_edge", feiler)
    monkeypatch.setattr(tale, "_say", feiler)
    with pytest.raises(tale.TaleFeil, match="«Salut»"):
        tale.lag_lyd("Salut", "fr", cache_dir=tmp_path)


@pytest.mark.skipif(not __import__("shutil").which("say"), reason="krever macOS say")
def test_say_ekte_med_vanskelig_tekst(tmp_path):
    ut = tmp_path / "x.aiff"
    tale._say("-là, d'où « ça » ?", "Thomas", "150", ut)
    assert ut.stat().st_size > 1000
```

- [ ] **Step 2: Kjør og se at de feiler**

Kjør: `uv run pytest tests/test_tale.py -q`
Forventet: FAIL med `ImportError`.

- [ ] **Step 3: Implementer**

```python
import asyncio
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

EDGE_STEMMER = {
    ("no", "a"): "nb-NO-FinnNeural",
    ("fr", "a"): "fr-FR-DeniseNeural",
    ("fr", "b"): "fr-FR-HenriNeural",
}
SAY_STEMMER = {("no", "a"): "Nora", ("fr", "a"): "Thomas", ("fr", "b"): "Jacques"}
EDGE_FART = {"sakte": "-20%", "normal": "+0%"}
SAY_FART = {"sakte": "150", "normal": "185"}

_edge_av = False


class TaleFeil(Exception):
    pass


def _edge(tekst: str, stemme_navn: str, fart: str, ut: Path) -> None:
    import edge_tts

    asyncio.run(edge_tts.Communicate(tekst, stemme_navn, rate=fart).save(str(ut)))


def _say(tekst: str, stemme_navn: str, fart: str, ut: Path) -> None:
    # Teksten går via fil så tegn som "-" først eller apostrof ikke tolkes som argumenter.
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as f:
        f.write(tekst)
    try:
        subprocess.run(
            ["say", "-v", stemme_navn, "-r", fart, "-o", str(ut), "-f", f.name],
            check=True,
            capture_output=True,
        )
    finally:
        Path(f.name).unlink(missing_ok=True)


def _nokkel(*deler: str) -> str:
    return hashlib.sha256("|".join(deler).encode("utf-8")).hexdigest()[:24]


def lag_lyd(
    tekst: str,
    sprak: str,
    fart: str = "sakte",
    stemme: str = "a",
    cache_dir: Path = Path(".cache"),
) -> Path:
    global _edge_av
    cache_dir.mkdir(parents=True, exist_ok=True)
    stemme = stemme if sprak == "fr" else "a"
    motorer = ["say"] if _edge_av else ["edge", "say"]

    for motor in motorer:
        filtype = "mp3" if motor == "edge" else "aiff"
        ut = cache_dir / f"{_nokkel(motor, sprak, fart, stemme, tekst)}.{filtype}"
        if ut.exists() and ut.stat().st_size > 0:
            return ut
        try:
            if motor == "edge":
                _edge(tekst, EDGE_STEMMER[(sprak, stemme)], EDGE_FART[fart], ut)
            else:
                _say(tekst, SAY_STEMMER[(sprak, stemme)], SAY_FART[fart], ut)
            if not ut.exists() or ut.stat().st_size == 0:
                raise TaleFeil("tom lydfil")
            return ut
        except Exception as e:
            ut.unlink(missing_ok=True)
            if motor == "edge":
                _edge_av = True
                print(f"edge-tts feilet ({e}). Bruker Mac-stemmene resten av kjøringen.", file=sys.stderr)
                continue
            raise TaleFeil(f"Klarte ikke lage lyd for «{tekst}»: {e}") from e
    raise TaleFeil(f"Klarte ikke lage lyd for «{tekst}»")
```

- [ ] **Step 4: Kjør testene**

Kjør: `uv run pytest tests/test_tale.py -q`
Forventet: alle PASS.

- [ ] **Step 5: Røyktest mot ekte edge-tts**

Kjør: `uv run python -c "from fransk.tale import lag_lyd; from pathlib import Path; print(lag_lyd(\"Vous venez d'où ?\", 'fr', cache_dir=Path('.cache')))"`
Forventet: skriver en sti som slutter på `.mp3`. Spill av med `afplay <sti>` og hør at det er fransk med kvinnestemme. Ender den på `.aiff`, feiler edge-tts. Noter feilmeldingen og si fra til brukeren før du går videre.

- [ ] **Step 6: Commit**

```bash
git add src/fransk/tale.py tests/test_tale.py
git commit -m "Legg til tale med edge-tts og say som reserve"
```

---

### Task 4: Lydsammensetting og bygging av episode

**Files:**
- Create: `src/fransk/lyd.py`, `src/fransk/bygg.py`
- Test: `tests/test_lyd.py`, `tests/test_bygg.py`

**Interfaces:**
- Consumes: `fransk.tale.lag_lyd`, `fransk.manus.Episode`, `fransk.config.PODKAST_TITTEL`
- Produces:
  - `fransk.lyd`: `class LydFeil(Exception)`, `krev_ffmpeg() -> None`, `sett_sammen(deler: list[Path | float], ut: Path, tittel: str, uke: int) -> None` (float = sekunder stillhet), `varighet(mp3: Path) -> int` (hele sekunder)
  - `fransk.bygg`: `MELLOMROM = 0.4`, `bygg_episode(ep: Episode, ut: Path, cache_dir: Path) -> None`

- [ ] **Step 1: Installer ffmpeg**

Kjør: `brew install ffmpeg`
Forventet: `ffmpeg -version` og `ffprobe -version` virker.

- [ ] **Step 2: Skriv feilende tester**

`tests/test_lyd.py`:

```python
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
```

`tests/test_bygg.py`:

```python
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
```

- [ ] **Step 3: Kjør og se at de feiler**

Kjør: `uv run pytest tests/test_lyd.py tests/test_bygg.py -q`
Forventet: FAIL med `ImportError`.

- [ ] **Step 4: Implementer `lyd.py`**

```python
import shutil
import subprocess
import tempfile
from pathlib import Path

from fransk.config import PODKAST_TITTEL


class LydFeil(Exception):
    pass


def krev_ffmpeg() -> None:
    for verktoy in ("ffmpeg", "ffprobe"):
        if shutil.which(verktoy) is None:
            raise LydFeil(f"Fant ikke {verktoy}. Installer med: brew install ffmpeg")


def _ffmpeg(*args: str) -> None:
    try:
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise LydFeil(f"ffmpeg feilet: {e.stderr.strip()}") from e


def sett_sammen(deler: list[Path | float], ut: Path, tittel: str, uke: int) -> None:
    krev_ffmpeg()
    ut.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        wavs = []
        for i, del_ in enumerate(deler):
            wav = tmp_dir / f"{i:05d}.wav"
            if isinstance(del_, Path):
                _ffmpeg("-i", str(del_), "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", str(wav))
            else:
                _ffmpeg(
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", f"{del_:.3f}", "-c:a", "pcm_s16le", str(wav),
                )
            wavs.append(wav)
        liste = tmp_dir / "liste.txt"
        liste.write_text("".join(f"file '{w}'\n" for w in wavs), encoding="utf-8")
        _ffmpeg(
            "-f", "concat", "-safe", "0", "-i", str(liste),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "64k",
            "-id3v2_version", "3",
            "-metadata", f"title={tittel}",
            "-metadata", f"album={PODKAST_TITTEL}",
            "-metadata", f"track={uke}",
            str(ut),
        )


def varighet(mp3: Path) -> int:
    krev_ffmpeg()
    resultat = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(mp3)],
        check=True,
        capture_output=True,
        text=True,
    )
    return round(float(resultat.stdout.strip()))
```

- [ ] **Step 5: Implementer `bygg.py`**

```python
from pathlib import Path

from fransk import lyd, tale
from fransk.manus import Episode

MELLOMROM = 0.4  # sekunder mellom to replikker som følger rett etter hverandre


def bygg_episode(ep: Episode, ut: Path, cache_dir: Path) -> None:
    deler: list[Path | float] = []
    forrige_var_tale = False
    for s in ep.segmenter:
        if s.type == "pause":
            deler.append(s.sekunder)
            forrige_var_tale = False
            continue
        if forrige_var_tale:
            deler.append(MELLOMROM)
        deler.append(tale.lag_lyd(s.tekst, s.type, s.fart, s.stemme, cache_dir))
        forrige_var_tale = True
    lyd.sett_sammen(deler, ut, tittel=f"Uke {ep.uke:02d}: {ep.tittel}", uke=ep.uke)
```

- [ ] **Step 6: Kjør testene**

Kjør: `uv run pytest tests/test_lyd.py tests/test_bygg.py -q`
Forventet: alle PASS.

- [ ] **Step 7: Commit**

```bash
git add src/fransk/lyd.py src/fransk/bygg.py tests/test_lyd.py tests/test_bygg.py
git commit -m "Legg til lydsammensetting og bygging av episode"
```

---

### Task 5: Podkastfeed

**Files:**
- Create: `src/fransk/feed.py`
- Test: `tests/test_feed.py`

**Interfaces:**
- Consumes: `fransk.manus.Episode`, `fransk.lyd.varighet`, `fransk.config`
- Produces: `beskrivelse(ep: Episode) -> str`, `publiseringstid(uke: int) -> datetime`, `lag_feed(episoder: list[Episode], lyd_dir: Path, base_url: str, varighet: Callable[[Path], int] | None = None) -> str` (hele XML-dokumentet). Bare episoder med `lyd_dir/uke-NN.mp3` tas med, nyeste først.

`pubDate` er `START_DATO + (uke − 1) uker` kl. 06:00 Oslo-tid. Da blir rekkefølgen i appen riktig selv om en gammel episode lages på nytt.

- [ ] **Step 1: Skriv feilende tester**

```python
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
```

- [ ] **Step 2: Kjør og se at de feiler**

Kjør: `uv run pytest tests/test_feed.py -q`
Forventet: FAIL med `ModuleNotFoundError`.

- [ ] **Step 3: Implementer**

```python
from collections.abc import Callable
from datetime import datetime, time, timedelta
from email.utils import format_datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

from fransk import lyd
from fransk.config import FORFATTER, PODKAST_BESKRIVELSE, PODKAST_TITTEL, START_DATO
from fransk.manus import Episode

ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ET.register_namespace("itunes", ITUNES)


def _it(navn: str) -> str:
    return f"{{{ITUNES}}}{navn}"


def beskrivelse(ep: Episode) -> str:
    linjer = [ep.beskrivelse, "", "Gloser:"]
    linjer += [f"- {o.fr}: {o.no}" for o in ep.gloser]
    linjer += ["", "Fraser:"]
    linjer += [f"- {o.fr}: {o.no}" for o in ep.fraser]
    linjer += ["", "Helgesamtale med Codex. Lim inn dette:", "", ep.codex_instruks]
    return "\n".join(linjer)


def publiseringstid(uke: int) -> datetime:
    dag = START_DATO + timedelta(weeks=uke - 1)
    return datetime.combine(dag, time(6, 0), tzinfo=ZoneInfo("Europe/Oslo"))


def lag_feed(
    episoder: list[Episode],
    lyd_dir: Path,
    base_url: str,
    varighet: Callable[[Path], int] | None = None,
) -> str:
    varighet = varighet or lyd.varighet
    rss = ET.Element("rss", {"version": "2.0"})
    kanal = ET.SubElement(rss, "channel")
    ET.SubElement(kanal, "title").text = PODKAST_TITTEL
    ET.SubElement(kanal, "link").text = base_url
    ET.SubElement(kanal, "description").text = PODKAST_BESKRIVELSE
    ET.SubElement(kanal, "language").text = "no"
    ET.SubElement(kanal, _it("author")).text = FORFATTER
    ET.SubElement(kanal, _it("image"), {"href": f"{base_url}/cover.jpg"})
    ET.SubElement(kanal, _it("category"), {"text": "Education"})
    ET.SubElement(kanal, _it("explicit")).text = "false"

    for ep in sorted(episoder, key=lambda e: e.uke, reverse=True):
        mp3 = lyd_dir / f"uke-{ep.uke:02d}.mp3"
        if not mp3.exists():
            continue
        url = f"{base_url}/lyd/{mp3.name}"
        item = ET.SubElement(kanal, "item")
        ET.SubElement(item, "title").text = f"Uke {ep.uke:02d}: {ep.tittel}"
        ET.SubElement(item, "description").text = beskrivelse(ep)
        ET.SubElement(
            item, "enclosure", {"url": url, "length": str(mp3.stat().st_size), "type": "audio/mpeg"}
        )
        ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = url
        ET.SubElement(item, "pubDate").text = format_datetime(publiseringstid(ep.uke))
        ET.SubElement(item, _it("duration")).text = str(varighet(mp3))
        ET.SubElement(item, _it("episode")).text = str(ep.uke)

    ET.indent(rss)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="unicode") + "\n"
```

- [ ] **Step 4: Kjør testene**

Kjør: `uv run pytest tests/test_feed.py -q`
Forventet: alle PASS.

- [ ] **Step 5: Commit**

```bash
git add src/fransk/feed.py tests/test_feed.py
git commit -m "Legg til podkastfeed"
```

---

### Task 6: Kommandolinje

**Files:**
- Create: `src/fransk/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `manus.manus_sti`, `manus.les_episode`, `manus.les_alle`, `manus.ManusFeil`, `repetisjon.velg_repetisjon`, `bygg.bygg_episode`, `lyd.varighet`, `lyd.LydFeil`, `tale.TaleFeil`, `feed.lag_feed`, `config.BASE_URL`
- Produces: `main(argv: list[str] | None = None) -> int`, `class PubliserFeil(Exception)`, `git_endringer(rot: Path) -> list[str]`. Kommandoer: `sjekk N`, `repetisjon N`, `lag N`, `publiser N`.

- [ ] **Step 1: Skriv feilende tester**

```python
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
```

- [ ] **Step 2: Kjør og se at de feiler**

Kjør: `uv run pytest tests/test_cli.py -q`
Forventet: FAIL med `ImportError`.

- [ ] **Step 3: Implementer**

```python
import argparse
import subprocess
import sys
from pathlib import Path

from fransk import lyd
from fransk.bygg import bygg_episode
from fransk.config import BASE_URL
from fransk.feed import lag_feed
from fransk.lyd import LydFeil
from fransk.manus import ManusFeil, les_alle, les_episode, manus_sti
from fransk.repetisjon import velg_repetisjon
from fransk.tale import TaleFeil


class PubliserFeil(Exception):
    pass


def _stier(rot: Path) -> dict[str, Path]:
    return {
        "manus": rot / "episoder",
        "lyd": rot / "docs" / "lyd",
        "feed": rot / "docs" / "feed.xml",
        "cache": rot / ".cache",
    }


def _mp3(rot: Path, uke: int) -> Path:
    return _stier(rot)["lyd"] / f"uke-{uke:02d}.mp3"


def sjekk(rot: Path, uke: int) -> int:
    sti = manus_sti(_stier(rot)["manus"], uke)
    les_episode(sti)
    print(f"{sti.name} er gyldig.")
    return 0


def repetisjon(rot: Path, uke: int) -> int:
    mappe = _stier(rot)["manus"]
    episoder = les_alle(mappe) if mappe.exists() else []
    valgt = velg_repetisjon(uke, episoder)
    if not valgt:
        print("Ingen tidligere gloser å repetere.")
    for kilde_uke, o in valgt:
        print(f"{o.fr} – {o.no} (uke {kilde_uke})")
    return 0


def lag(rot: Path, uke: int) -> int:
    stier = _stier(rot)
    ep = les_episode(manus_sti(stier["manus"], uke))
    ut = _mp3(rot, uke)
    bygg_episode(ep, ut, stier["cache"])
    minutter = lyd.varighet(ut) / 60
    print(f"Laget {ut.relative_to(rot)} ({minutter:.1f} min).")
    return 0


def _git(rot: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", *args], cwd=rot, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise PubliserFeil(f"git {' '.join(args)} feilet: {e.stderr.strip()}") from e


def git_endringer(rot: Path) -> list[str]:
    linjer = _git(rot, "status", "--porcelain", "-uall").stdout.splitlines()
    return [linje[3:].split(" -> ")[-1] for linje in linjer if linje.strip()]


def publiser(rot: Path, uke: int) -> int:
    stier = _stier(rot)
    tillatt = (f"episoder/uke-{uke:02d}.yaml", "docs/")
    andre = [p for p in git_endringer(rot) if not p.startswith(tillatt)]
    if andre:
        raise PubliserFeil("Uncommittede endringer utenfor episoden: " + ", ".join(andre))

    if not _mp3(rot, uke).exists():
        lag(rot, uke)
    stier["feed"].parent.mkdir(parents=True, exist_ok=True)
    stier["feed"].write_text(lag_feed(les_alle(stier["manus"]), stier["lyd"], BASE_URL), encoding="utf-8")

    _git(rot, "add", f"episoder/uke-{uke:02d}.yaml", "docs")
    har_endringer = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=rot).returncode != 0
    if har_endringer:
        _git(rot, "commit", "-q", "-m", f"Publiser uke {uke:02d}")
    else:
        print("Ingenting nytt å committe.")
    _git(rot, "push", "-q")
    print(f"Publisert. Feed: {BASE_URL}/feed.xml")
    return 0


KOMMANDOER = {"sjekk": sjekk, "repetisjon": repetisjon, "lag": lag, "publiser": publiser}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fransk", description="Fransk på løpetur")
    sub = parser.add_subparsers(dest="kommando", required=True)
    for navn in KOMMANDOER:
        sub.add_parser(navn).add_argument("uke", type=int)
    args = parser.parse_args(argv)
    try:
        return KOMMANDOER[args.kommando](Path.cwd(), args.uke)
    except (ManusFeil, TaleFeil, LydFeil, PubliserFeil) as e:
        print(f"Feil: {e}", file=sys.stderr)
        return 1
```

Merk: `test_publiser_to_ganger_krasjer_ikke` sjekker utskriften «Ingenting nytt». Begge kjøringer skriver til samme `capsys`, så teksten fra andre kjøring er med.

- [ ] **Step 4: Kjør hele testsuiten**

Kjør: `uv run pytest -q`
Forventet: alle PASS.

- [ ] **Step 5: Commit**

```bash
git add src/fransk/cli.py tests/test_cli.py
git commit -m "Legg til kommandolinje"
```

---

### Task 7: Pensum, skriveregler og første episode

**Files:**
- Create: `CLAUDE.md`, `pensum.md`, `episoder/uke-01.yaml`, `docs/cover.jpg`, `docs/.nojekyll`

**Interfaces:**
- Consumes: `uv run fransk sjekk|repetisjon|lag` fra Task 6
- Produces: en ferdig `docs/lyd/uke-01.mp3` som brukeren har hørt gjennom

- [ ] **Step 1: Skriv `CLAUDE.md`**

Dette er instruksen fremtidige Claude-økter følger når brukeren sier «lag neste episode».

````markdown
# Fransk på løpetur

Ukentlige franskleksjoner som podkast. Brukeren hører episoden på to rolige løpeturer (ca. 25 min) og øver i helgen med Codex sin talemodell. Mål: småprat med franske turister i Norge, deretter som turist i Frankrike. Nivå: litt skolefransk.

Spec: `design/specs/2026-10-04-fransk-podkast-design.md`

## Når brukeren ber om neste episode

1. Finn neste uke N (høyeste `episoder/uke-NN.yaml` + 1).
2. Les `pensum.md` for temaet til uke N og de to siste manusene for nivå og tone.
3. Kjør `uv run fransk repetisjon N` og bruk glosene i repetisjonsdelen.
4. Skriv `episoder/uke-NN.yaml` etter reglene under.
5. Kjør `uv run fransk sjekk N`, så `uv run fransk lag N`. Varigheten skal være 20–25 min. Er den under 18 eller over 27, juster manuset og lag på nytt.
6. Vis brukeren gloser, fraser og varighet. Publiser med `uv run fransk publiser N` først når brukeren sier ja.
7. Marker uka som ferdig i `pensum.md` og commit.

## Episodeformat

| Del | Varighet | Innhold |
|---|---|---|
| 1. Intro | 0,5 min | Uke, tema og hva lytteren skal klare etter episoden |
| 2. Repetisjon | 3 min | Glosene fra `fransk repetisjon N`. Norsk ord, `pause: 3`, fransk ord. Uke 1 hopper over denne delen. |
| 3. Ukas 10 gloser | 7 min | Fransk to ganger sakte, betydning, kort uttaletips, eksempelsetning |
| 4. Ukas fraser | 6 min | 6–8 fraser som bruker glosene. Lange fraser bygges bakfra. |
| 5. Dialog | 4 min | To franske stemmer (`stemme: a` og `b`). Først sakte med norske forklaringer innimellom, så i `fart: normal` uten avbrudd. |
| 6. Avslutning | 2 min | Alle 10 gloser: norsk, `pause: 3`, fransk. Så helgeoppdraget. |

## Skriveregler

- Norsk stemme forklarer, fransk stemme sier alt på fransk. Bland aldri språk i ett segment, for talemotoren uttaler da feil.
- Etter hver fransk frase som lytteren kan mumle med: `pause: 2` eller `pause: 3`.
- Uttaletips skrives på norsk med norske lydbilder: «r-en sitter bak i halsen», «s-en på slutten er stum», «on uttales gjennom nesen».
- Bakfra-bygging: `lentement` → `plus lentement` → `parler plus lentement` → `Vous pouvez parler plus lentement ?`
- Gloser og fraser i en uke skal kunne brukes i en ekte samtale med en turist. Unngå bokord.
- Bruk «vous» mot turister. Introduser «tu» først når pensum sier det.
- Fransk tegnsetting: mellomrom før `?`, `!` og `:`.
- `fart: sakte` til og med uke 8. Fra uke 9 kan forklarende fransk være `normal`, og dialogens andre runde er alltid `normal`.
- Fra uke 6 kan faste vendinger sies på fransk: «Le mot suivant», «Encore une fois», «Écoutez».

## Codex-instruks

Fyll inn malen og legg den i `codex_instruks`:

```
Du er <rolle>, en fransk turist <situasjon>. Jeg er nordmann og lærer fransk. Jeg har litt skolefransk og er på uke <N>.
Snakk bare fransk, sakte og med korte, enkle setninger. Hold deg så langt det går til disse ordene og frasene: <ukas gloser og fraser, og et utvalg fra tidligere uker>.
Etter hvert svar fra meg: hvis jeg sa noe feil, gi en kort rettelse på norsk i én setning, og fortsett så samtalen på fransk.
Du starter samtalen. Etter rundt 10 minutter avslutter du og sier på norsk hvilke tre ting jeg bør øve mer på.
```
````

- [ ] **Step 2: Skriv `pensum.md`**

```markdown
# Pensum

Kryss av når episoden er publisert. Juster temaene underveis.

## Turister i Norge

- [ ] Uke 1: Hei, hvor kommer du fra? Hilse, presentere seg, snakke litt fransk, be om saktere tale
- [ ] Uke 2: Er det første gang i Norge? Hvor lenge, liker dere dere
- [ ] Uke 3: Hva jeg heter og hva jeg gjør. Jobb, bosted, alder
- [ ] Uke 4: Tall 1–100 og tid. Hvor mange dager, klokka
- [ ] Uke 5: Tips om Oslo. Operaen, Vigelandsparken, fjorden, «je vous conseille»
- [ ] Uke 6: Været. Det regner, det er kaldt, i morgen blir det fint
- [ ] Uke 7: Tips om Norge. Bergen, fjordene, nordlys, Hurtigruten
- [ ] Uke 8: Fritid. Løping, tur, ski, «j'aime»
- [ ] Uke 9: Familie. Barn, partner, søsken
- [ ] Uke 10: Hjelpe en turist. Veien til stasjonen, kjøpe billett
- [ ] Uke 11: Mat i Norge. Brunost, laks, pris
- [ ] Uke 12: Samle trådene. Lang småprat med alt fra uke 1–11

## Turist i Frankrike

- [ ] Uke 13: Kafé. Bestille kaffe og croissant, betale
- [ ] Uke 14: Restaurant. Bord, meny, allergier, regningen
- [ ] Uke 15: Butikk og marked. Pris, størrelse, «je regarde seulement»
- [ ] Uke 16: Hotell. Sjekke inn, reservasjon, frokost, problemer med rommet
- [ ] Uke 17: Veibeskrivelse. Til venstre, rett fram, langt unna
- [ ] Uke 18: Transport. Metro, tog, billett, forsinkelse
- [ ] Uke 19: Småprat med franskmenn. Hvor kommer du fra, jeg er fra Norge
- [ ] Uke 20: Samle trådene. En dag som turist

## Holde samtalen gående

- [ ] Uke 21: Fortid 1. «J'ai visité», «j'ai mangé»
- [ ] Uke 22: Fortid 2. «Je suis allé», «nous sommes arrivés»
- [ ] Uke 23: Følge opp. «Ah bon ?», «C'est vrai ?», «Et vous ?»
- [ ] Uke 24: Fortelle om en tur
- [ ] Uke 25: Planer. «Je vais…», i morgen, neste uke
- [ ] Uke 26: Samle trådene. Lang samtale
```

- [ ] **Step 3: Lag forsidebilde og `.nojekyll`**

Kjør:

```bash
mkdir -p docs && touch docs/.nojekyll
ffmpeg -loglevel error -y -f lavfi -i color=c=0x1d3557:s=1400x1400 -frames:v 1 \
  -vf "drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial Bold.ttf:text='Fransk':fontcolor=white:fontsize=220:x=(w-text_w)/2:y=h/2-240,drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial Bold.ttf:text='på løpetur':fontcolor=0xe63946:fontsize=150:x=(w-text_w)/2:y=h/2+40" \
  docs/cover.jpg
```

Forventet: `docs/cover.jpg` finnes. Åpne med `open docs/cover.jpg` og se at teksten står. Feiler `drawtext` (ffmpeg uten freetype), fjern `-vf ...` og lag en ensfarget forside i stedet.

- [ ] **Step 4: Skriv `episoder/uke-01.yaml`**

Følg `CLAUDE.md`. Uke 1 har ingen repetisjonsdel. Bruk disse glosene og frasene:

```yaml
uke: 1
tittel: "Hei, hvor kommer du fra?"
beskrivelse: "Hilse, presentere seg, spørre hvor folk kommer fra og be om at de snakker saktere."
gloser:
  - { fr: "bonjour", no: "hei, god dag" }
  - { fr: "merci", no: "takk" }
  - { fr: "oui", no: "ja" }
  - { fr: "non", no: "nei" }
  - { fr: "je m'appelle", no: "jeg heter" }
  - { fr: "français", no: "fransk" }
  - { fr: "la Norvège", no: "Norge" }
  - { fr: "d'où", no: "hvorfra" }
  - { fr: "un peu", no: "litt" }
  - { fr: "lentement", no: "sakte" }
fraser:
  - { fr: "Bonjour, vous êtes français ?", no: "Hei, er dere franske?" }
  - { fr: "Je m'appelle Edvard.", no: "Jeg heter Edvard." }
  - { fr: "Vous venez d'où ?", no: "Hvor kommer dere fra?" }
  - { fr: "Je suis de Norvège, j'habite à Oslo.", no: "Jeg er fra Norge, jeg bor i Oslo." }
  - { fr: "Je parle un peu français.", no: "Jeg snakker litt fransk." }
  - { fr: "Vous pouvez parler plus lentement, s'il vous plaît ?", no: "Kan du snakke litt saktere?" }
  - { fr: "Enchanté !", no: "Hyggelig å hilse på deg!" }
```

Dialog (del 5): Edvard (stemme a) møter en fransk turist (stemme b) ved Operaen i Oslo og bruker frasene over. Codex-instruksen: rollen er en fransk turist som står og ser på utsikten fra taket på Operaen.

- [ ] **Step 5: Sjekk, lag og mål**

Kjør: `uv run fransk sjekk 1 && uv run fransk lag 1`
Forventet: `Laget docs/lyd/uke-01.mp3 (X min)` der X er mellom 18 og 27. Hvis ikke, juster manuset (flere eller færre eksempelsetninger og pauser) og kjør igjen.

- [ ] **Step 6: Brukeren hører gjennom**

Spill av med `afplay docs/lyd/uke-01.mp3` eller åpne filen. Be brukeren lytte og si fra om stemmer, tempo, pauselengde og lydnivå. Juster manus eller konstanter (`EDGE_FART`, `MELLOMROM`, pauser) til brukeren er fornøyd.

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md pensum.md episoder/uke-01.yaml docs/cover.jpg docs/.nojekyll
git commit -m "Legg til pensum, skriveregler og første episode"
```

MP3-filen og feeden committes av `fransk publiser` i Task 8.

---

### Task 8: GitHub Pages og publisering

**Files:**
- Ingen nye kildefiler. Oppretter GitHub-repoet og publiserer uke 1.

**Interfaces:**
- Consumes: `uv run fransk publiser 1`
- Produces: en fungerende feed på `https://edvardunsvag.github.io/fransk-podkast/feed.xml`

- [ ] **Step 1: Bekreft med brukeren**

Repoet blir offentlig. Spør brukeren om å opprette `Edvardunsvag/fransk-podkast` som offentlig repo før du kjører neste steg.

- [ ] **Step 2: Opprett repo og push**

```bash
gh repo create Edvardunsvag/fransk-podkast --public --source . --remote origin
git push -u origin main
```

- [ ] **Step 3: Publiser uke 1**

Kjør: `uv run fransk publiser 1`
Forventet: `Publisert. Feed: https://edvardunsvag.github.io/fransk-podkast/feed.xml`

- [ ] **Step 4: Slå på GitHub Pages**

```bash
gh api -X POST repos/Edvardunsvag/fransk-podkast/pages -f "source[branch]=main" -f "source[path]=/docs"
```

Forventet: JSON med `"html_url": "https://edvardunsvag.github.io/fransk-podkast/"`.

- [ ] **Step 5: Verifiser feeden**

Vent til Pages er bygget (`gh api repos/Edvardunsvag/fransk-podkast/pages --jq .status` gir `built`), så:

```bash
curl -sf https://edvardunsvag.github.io/fransk-podkast/feed.xml | head -20
curl -sfI https://edvardunsvag.github.io/fransk-podkast/lyd/uke-01.mp3 | head -5
curl -sfI https://edvardunsvag.github.io/fransk-podkast/cover.jpg | head -5
```

Forventet: feeden vises, og MP3 og forside gir `HTTP/2 200`.

- [ ] **Step 6: Brukeren tester på mobil og klokke**

Be brukeren:

1. Legge til feeden i podkastappen via «Legg til med URL» (Apple Podcasts: Bibliotek → … → Følg en serie via URL). Se at uke 1 dukker opp med forside, beskrivelse og Codex-instruks.
2. Overføre `docs/lyd/uke-01.mp3` til Garmin-klokka med Garmin Express (Musikk → legg til fra mappe), og spille av en bit uten telefon.

Noter resultatet. Hvis noe feiler, finn årsaken før planen regnes som ferdig.
