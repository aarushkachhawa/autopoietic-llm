from solution import fizzbuzz


def test_small():
    assert fizzbuzz(5) == ["1", "2", "Fizz", "4", "Buzz"]


def test_fizzbuzz_at_15():
    assert fizzbuzz(15)[-1] == "FizzBuzz"


def test_one():
    assert fizzbuzz(1) == ["1"]
