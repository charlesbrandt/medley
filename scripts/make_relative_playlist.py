#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2012.09.07 10:55:59 
# License:  MIT 

# Requires:
# mindstream, copy_media.py, probably moments too

# Description:
#
# script to generate a m3u instead of copy media
# previously this required manually toggling an attribute
# in the copy_media script

"""
from __future__ import print_function
import sys, os, re
from copy_media import process_files

from moments.path import Path

def usage():
    print(__doc__)
    
def main():
    if len (sys.argv) > 1:
        if sys.argv[1] in ['--help','help', '-h', '--h', '-help']:
            usage()
        f1 = sys.argv[1]
        translate = None
        if len(sys.argv) > 2:
            translate = sys.argv[2]

        source = Path(f1)
        destination = os.path.abspath("./%s" % source.filename)
        print(source)
        print(destination)
        if source != destination:
            process_files(f1, translate, action="m3u", m3u_dest=destination)
        else:
            process_files(f1, translate, action="m3u")

if __name__ == '__main__':
    #see copy_media.py for related functionality
    main()
