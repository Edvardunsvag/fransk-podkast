from fransk.manus import Episode, Ord


def kjente_ord(uke: int, episoder: list[Episode]) -> list[tuple[int, Ord]]:
    """Gloser og forklarte ord fra alle uker før `uke`, i ukerekkefølge."""
    kjente: list[tuple[int, Ord]] = []
    for ep in sorted(episoder, key=lambda e: e.uke):
        if ep.uke < uke:
            kjente += [(ep.uke, o) for o in ep.gloser + ep.andre_ord]
    return kjente
