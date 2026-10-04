from conftest import gyldig_data
from fransk.manus import Episode, Ord, _valider
from fransk.repetisjon import velg_repetisjon


def ep(uke: int) -> Episode:
    return _valider(gyldig_data(uke), f"uke-{uke:02d}.yaml")


def test_uke_1_har_ingen_repetisjon():
    assert velg_repetisjon(1, [ep(1)]) == []


def test_uke_2_tar_8_fra_uke_1():
    valgt = velg_repetisjon(2, [ep(1), ep(2)])
    assert valgt == [(1, Ord(f"mot1-{i}", f"ord1-{i}")) for i in range(8)]


def test_uke_3_deler_jevnt_og_forskyver_start():
    valgt = velg_repetisjon(3, [ep(1), ep(2), ep(3)])
    assert len(valgt) == 8
    fra_uke_2 = [o.fr for u, o in valgt if u == 2]
    fra_uke_1 = [o.fr for u, o in valgt if u == 1]
    assert fra_uke_2 == ["mot2-0", "mot2-1", "mot2-2", "mot2-3"]
    assert fra_uke_1 == ["mot1-2", "mot1-3", "mot1-4", "mot1-5"]


def test_uke_9_bruker_1_2_4_8_uker_tilbake():
    episoder = [ep(u) for u in range(1, 10)]
    valgt = velg_repetisjon(9, episoder)
    assert sorted({u for u, _ in valgt}) == [1, 5, 7, 8]
    assert len(valgt) == 8
    assert [o.fr for u, o in valgt if u == 1] == ["mot1-7", "mot1-8"]


def test_manglende_uke_hoppes_over():
    valgt = velg_repetisjon(5, [ep(1), ep(4)])
    assert {u for u, _ in valgt} == {1, 4}
    assert len(valgt) == 8
