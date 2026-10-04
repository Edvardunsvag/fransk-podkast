from conftest import gyldig_data
from fransk.kjente import kjente_ord
from fransk.manus import Ord, _valider


def ep(uke, andre=()):
    data = gyldig_data(uke)
    if andre:
        data["andre_ord"] = [{"fr": f, "no": n} for f, n in andre]
    return _valider(data, f"uke-{uke:02d}.yaml")


def test_tar_med_gloser_og_andre_ord_fra_tidligere_uker():
    episoder = [ep(1, [("venir", "å komme")]), ep(2), ep(3)]
    kjente = kjente_ord(3, episoder)
    assert (1, Ord("mot1-0", "ord1-0")) in kjente
    assert (1, Ord("venir", "å komme")) in kjente
    assert (2, Ord("mot2-9", "ord2-9")) in kjente
    assert all(uke < 3 for uke, _ in kjente)
    assert len(kjente) == 21


def test_uke_1_har_ingen_kjente_ord():
    assert kjente_ord(1, [ep(1)]) == []
