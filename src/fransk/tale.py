import asyncio
import hashlib
import os
import subprocess
import sys
import tempfile
import urllib.request
from html import escape
from pathlib import Path

EDGE_STEMMER = {
    ("no", "a"): "nb-NO-FinnNeural",
    ("fr", "a"): "fr-FR-DeniseNeural",
    ("fr", "b"): "fr-FR-HenriNeural",
}
SAY_STEMMER = {("no", "a"): "Nora", ("fr", "a"): "Thomas", ("fr", "b"): "Jacques"}
EDGE_FART = {"sakte": "-20%", "normal": "+0%"}
SAY_FART = {"sakte": "150", "normal": "185"}

AZURE_RESSURS = ("edvard.unsvag", "fransk-podkast-speech")
AZURE_REGION = "swedencentral"
AZURE_SPRAK = {"no": "nb-NO", "fr": "fr-FR"}

_edge_av = False
_azure_nokkel: str | None = None


class TaleFeil(Exception):
    pass


def _edge(tekst: str, stemme_navn: str, fart: str, ut: Path) -> None:
    import edge_tts

    asyncio.run(edge_tts.Communicate(tekst, stemme_navn, rate=fart).save(str(ut)))


def _azure_key() -> str:
    global _azure_nokkel
    if _azure_nokkel is None:
        _azure_nokkel = os.environ.get("AZURE_SPEECH_KEY") or subprocess.run(
            ["az", "cognitiveservices", "account", "keys", "list",
             "-g", AZURE_RESSURS[0], "-n", AZURE_RESSURS[1], "--query", "key1", "-o", "tsv"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    return _azure_nokkel


def _azure(tekst: str, sprak: str, stemme_navn: str, fart: str, ut: Path) -> None:
    ssml = (
        f"<speak version='1.0' xml:lang='{AZURE_SPRAK[sprak]}'>"
        f"<voice name='{stemme_navn}'><prosody rate='{fart}'>{escape(tekst)}</prosody></voice></speak>"
    )
    req = urllib.request.Request(
        f"https://{AZURE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1",
        data=ssml.encode("utf-8"),
        headers={
            "Ocp-Apim-Subscription-Key": _azure_key(),
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
            "User-Agent": "fransk-podkast",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as svar:
        ut.write_bytes(svar.read())


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
    motorer = ["azure", "say"] if _edge_av else ["edge", "azure", "say"]

    for motor in motorer:
        filtype = "aiff" if motor == "say" else "mp3"
        ut = cache_dir / f"{_nokkel(motor, sprak, fart, stemme, tekst)}.{filtype}"
        if ut.exists() and ut.stat().st_size > 0:
            return ut
        try:
            if motor == "edge":
                _edge(tekst, EDGE_STEMMER[(sprak, stemme)], EDGE_FART[fart], ut)
            elif motor == "azure":
                _azure(tekst, sprak, EDGE_STEMMER[(sprak, stemme)], EDGE_FART[fart], ut)
            else:
                _say(tekst, SAY_STEMMER[(sprak, stemme)], SAY_FART[fart], ut)
            if not ut.exists() or ut.stat().st_size == 0:
                raise TaleFeil("tom lydfil")
            return ut
        except Exception as e:
            ut.unlink(missing_ok=True)
            if motor == "edge":
                _edge_av = True
                print(f"edge-tts feilet ({e}). Bruker Azure Speech resten av kjøringen.", file=sys.stderr)
                continue
            if motor == "azure":
                print(f"Azure Speech feilet ({e}). Bruker Mac-stemmene for denne frasen.", file=sys.stderr)
                continue
            raise TaleFeil(f"Klarte ikke lage lyd for «{tekst}»: {e}") from e
    raise TaleFeil(f"Klarte ikke lage lyd for «{tekst}»")
