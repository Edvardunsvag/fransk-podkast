import argparse
import subprocess
import sys
from pathlib import Path

from fransk import lyd
from fransk.bygg import bygg_episode
from fransk.config import BASE_URL
from fransk.feed import lag_feed
from fransk.kjente import kjente_ord
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


def kjente(rot: Path, uke: int) -> int:
    mappe = _stier(rot)["manus"]
    episoder = les_alle(mappe) if mappe.exists() else []
    ord_ = kjente_ord(uke, episoder)
    if not ord_:
        print("Ingen kjente ord ennå.")
    for kilde_uke, o in ord_:
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


KOMMANDOER = {"sjekk": sjekk, "repetisjon": repetisjon, "kjente": kjente, "lag": lag, "publiser": publiser}


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
