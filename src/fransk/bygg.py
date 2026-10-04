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
