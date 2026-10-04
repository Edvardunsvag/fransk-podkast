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
