#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2015.03.19 19:04:52 
# License: MIT 

# Requires:
#

# Description:
#
this functionality is now a method on the Content object itself
adapted from split_media script
"""
from __future__ import print_function

import os, sys, codecs

def usage():
    print(__doc__)
    
if __name__ == '__main__':
    source = None
    destination = None
    if len(sys.argv) > 1:
        helps = ['--help', 'help', '-h']
        for i in helps:
            if i in sys.argv:
                usage()
                exit()
        source = sys.argv[1]
        if len(sys.argv) > 2:
            destination = sys.argv[2]
        else:
            destination = None

    #extract_segment(segment)

