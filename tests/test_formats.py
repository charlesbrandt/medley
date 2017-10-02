from __future__ import print_function
from builtins import object
import sys, os
# one directory up
_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
_module_dir = os.path.join(_root_dir, "medley")
sys.path.insert(0, _module_dir)

from formats import M3U
from moments.filters import to_ascii2

#for assert_equal
from nose.tools import *

class TestM3U(object):
    def setUp(self):
        a = True
        #self.c = sources.Converter()

    def test_load(self):
        m = M3U("sample.m3u")
        print(m)
        for content in m:
            #print to_ascii2(content.marks)
            print(len(content.marks))
            assert (len(content.marks) == 43) or (len(content.marks) == 12)
        assert len(m) == 2

    def test_save(self):
        m = M3U("sample.m3u")
        m.save("temp.m3u")
        assert os.path.exists("temp.m3u")
        m2 = M3U("temp.m3u")
        assert len(m2) == 2
        #assert False

    ## def test_m3u(self):
    ##     s = self.c.from_m3u("zoobar/sample.m3u")
    ##     print len(s)
    ##     m3u = self.c.to_m3u(s, verify=False)
    ##     f = open("zoobar/temp.m3u", 'w')
    ##     f.write(m3u)
    ##     f.close()
    ##     s2 = self.c.from_m3u("zoobar/temp.m3u")
        
    ##     assert len(s) == 21
    ##     assert len(s2) == 21
        
        
        
        
