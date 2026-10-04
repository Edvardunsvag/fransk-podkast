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
