from tests4py.tests.diversity import Systemtests


class TestsFailing(Systemtests):
    def __init__(self):
        super().__init__(passing=False)

    def test_diversity_1(self):
        return "-otest.log -cint=str"

    def test_diversity_2(self):
        return "-cint=str"

    def test_diversity_3(self):
        return "-T -d1 -cint=repr"

    def test_diversity_4(self):
        return "-o -d1 -cbool=str"

    def test_diversity_5(self):
        return "-O -otest.log -cint=repr,bool=str"

    def test_diversity_6(self):
        return "-d1 -wx -cfloat=str"

    def test_diversity_7(self):
        return "-wy -cstr=str"

    def test_diversity_8(self):
        return "-otest.log -wx -cstr=int"

    def test_diversity_9(self):
        return "-ptest -cbool=int"

    def test_diversity_10(self):
        return "-ptest -wx -cint=str"


class TestsPassing(Systemtests):
    def __init__(self):
        super().__init__(passing=True)

    def test_diversity_1(self):
        return "-otest.log"

    def test_diversity_2(self):
        return ""

    def test_diversity_3(self):
        return "-T -d1"

    def test_diversity_4(self):
        return "-o -d1"

    def test_diversity_5(self):
        return "-O -otest.log"

    def test_diversity_6(self):
        return "-d1 -wx"

    def test_diversity_7(self):
        return "-wy"

    def test_diversity_8(self):
        return "-otest.log -wx"

    def test_diversity_9(self):
        return "-ptest"

    def test_diversity_10(self):
        return "-ptest -wx"
