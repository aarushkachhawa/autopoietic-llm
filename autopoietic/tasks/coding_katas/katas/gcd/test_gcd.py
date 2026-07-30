from solution import gcd


def test_basic():
    assert gcd(48, 18) == 6


def test_coprime():
    assert gcd(17, 5) == 1


def test_zero():
    assert gcd(0, 5) == 5
