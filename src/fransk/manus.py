from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

TOPP_FELT = {"uke", "tittel", "beskrivelse", "gloser", "fraser", "codex_instruks", "segmenter"}
VALGFRIE_FELT = {"andre_ord"}
SEGMENT_FELT = {"no", "fr", "pause", "fart", "stemme"}


class _Laster(yaml.SafeLoader):
    """SafeLoader der bare true/false er boolske verdier, så nøkkelen `no` forblir tekst."""


_Laster.yaml_implicit_resolvers = {
    tegn: [(tag, regex) for tag, regex in resolvere if tag != "tag:yaml.org,2002:bool"]
    for tegn, resolvere in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_Laster.add_implicit_resolver(
    "tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), list("tTfF")
)


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
    andre_ord: list[Ord] = field(default_factory=list)


def manus_sti(mappe: Path, uke: int) -> Path:
    return mappe / f"uke-{uke:02d}.yaml"


def les_episode(sti: Path) -> Episode:
    if not sti.exists():
        raise ManusFeil(f"Finner ikke manus: {sti}")
    try:
        data = yaml.load(sti.read_text(encoding="utf-8"), Loader=_Laster)
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
    ukjente = data.keys() - TOPP_FELT - VALGFRIE_FELT
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

    andre_ord = _ordliste(data.get("andre_ord", []), "andre_ord", feil)

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
        andre_ord=andre_ord,
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
