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
