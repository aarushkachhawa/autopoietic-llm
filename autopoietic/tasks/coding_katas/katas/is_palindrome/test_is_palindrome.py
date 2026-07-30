from solution import is_palindrome


def test_simple_true():
    assert is_palindrome("level") is True


def test_simple_false():
    assert is_palindrome("hello") is False


def test_ignores_case_and_punctuation():
    assert is_palindrome("A man, a plan, a canal: Panama") is True
