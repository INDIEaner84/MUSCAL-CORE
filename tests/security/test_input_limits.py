import pytest
from mkc import mkc, MAX_INPUT_LENGTH


class TestInputLimits:
    def test_normal_input_works(self):
        result = mkc("print hello")
        assert result is not None

    def test_oversized_input_raises(self):
        with pytest.raises(ValueError, match="exceeds max length"):
            mkc("a" * (MAX_INPUT_LENGTH + 1))

    def test_input_at_exact_limit(self):
        result3 = mkc("x" * MAX_INPUT_LENGTH)
        assert result3 is not None

    def test_null_byte_rejected(self):
        with pytest.raises(ValueError, match="null byte"):
            mkc("hello\0world")

    def test_null_byte_in_raw_input_rejected(self):
        with pytest.raises(ValueError, match="null byte"):
            mkc("print hello", raw_input="bad\0input")

    def test_oversized_raw_input_rejected(self):
        with pytest.raises(ValueError, match="exceeds max length"):
            mkc("print hello", raw_input="x" * (MAX_INPUT_LENGTH + 1))
