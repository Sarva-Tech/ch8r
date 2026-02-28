import pytest


class TestBasic:
    @pytest.mark.unit
    def test_math(self):
        assert 2 + 2 == 4
        assert 1 + 1 == 2
        assert 3 * 2 == 6

    @pytest.mark.unit
    def test_strings(self):
        assert "hello" + "world" == "helloworld"
        assert len("test") == 4
        assert "test".upper() == "TEST"

    @pytest.mark.unit
    def test_lists(self):
        my_list = [1, 2, 3, 4]
        assert len(my_list) == 4
        assert my_list[0] == 1
        assert 5 not in my_list
