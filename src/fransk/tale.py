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
