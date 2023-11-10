from tests4py.tests.diversity import FailingSystemtests, PassingSystemtests


class TestsFailing(FailingSystemtests):
    def test_diversity_1(self):
        return " ( 30 / 5 ) / ( 3 - 3 ) "

    def test_diversity_2(self):
        return " ( 3 * 5 ) / 0 "

    def test_diversity_3(self):
        return " 3 / ( 4 - 4 ) "

    def test_diversity_4(self):
        return " ( 21 / 7 ) / ( 0 * 2 ) "

    def test_diversity_5(self):
        return " ( 10 / 5 ) / ( 5 - 5 ) "

    def test_diversity_6(self):
        return " ( 11 + 11 ) / ( 3 / 0 ) "

    def test_diversity_7(self):
        return " ( 40 / 4 ) / ( 10 * 0 ) "

    def test_diversity_8(self):
        return " ( 13 + 31 ) / ( 0 / 5 ) "

    def test_diversity_9(self):
        return " ( 5 + 2 ) / 0 "

    def test_diversity_10(self):
        return " ( 11 - 6 ) / ( 10 - 10 ) "


class TestsPassing(PassingSystemtests):
    def test_diversity_1(self):
        return " ( 30 / 5 ) / ( 3 + 3 ) "

    def test_diversity_2(self):
        return " ( 30 / 5 ) / ( 3 + 3 ) "

    def test_diversity_3(self):
        return " ( 30 / 5 ) / ( 3 + 3 ) "

    def test_diversity_4(self):
        return " ( 30 / 5 ) / ( 3 + 3 ) "

    def test_diversity_5(self):
        return " ( 30 / 5 ) / ( 3 + 3 ) "

    def test_diversity_6(self):
        return " ( 30 / 5 ) / ( 3 + 3 ) "

    def test_diversity_7(self):
        return " ( 30 / 5 ) / ( 3 + 3 ) "

    def test_diversity_8(self):
        return " ( 30 / 5 ) / ( 3 + 3 ) "

    def test_diversity_9(self):
        return " ( 30 / 5 ) / ( 3 + 3 ) "

    def test_diversity_10(self):
        return " ( 30 / 5 ) / ( 3 + 3 ) "
