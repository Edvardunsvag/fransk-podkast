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
        tmp_ut = ut.with_suffix(".tmp.mp3")
        try:
            _ffmpeg(
                "-f", "concat", "-safe", "0", "-i", str(liste),
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "64k",
                "-id3v2_version", "3",
                "-metadata", f"title={tittel}",
                "-metadata", f"album={PODKAST_TITTEL}",
                "-metadata", f"track={uke}",
                str(tmp_ut),
            )
        except BaseException:
            tmp_ut.unlink(missing_ok=True)
            raise
        tmp_ut.replace(ut)


def varighet(mp3: Path) -> int:
    krev_ffmpeg()
    try:
        resultat = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(mp3)],
            check=True,
            capture_output=True,
            text=True,
        )
        return round(float(resultat.stdout.strip()))
    except (subprocess.CalledProcessError, ValueError) as e:
        raise LydFeil(f"Kan ikke lese {mp3.name}. Slett filen og kjør fransk lag på nytt.") from e
