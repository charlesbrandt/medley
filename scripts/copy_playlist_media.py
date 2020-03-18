#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2013.06.05 
# License: MIT 

# Requires:
# medley, moments

# Description:
#

# be sure to edit source_root and destination_root before running, then run:
cd ~/public/repos/medley/scripts
python copy_playlist_media.py /media/path/to.m3u

copy_media(source, source_root, destination_root)


useful to use:

afterwards to update the original playlist to the new location:
python /c/medley/scripts/filter_m3u_path.py /media/path/to.m3u /media/previous/base/:/media/new/base/
"""
from __future__ import print_function
from builtins import str
import os, sys, codecs
import re, shutil

from medley.formats import M3U

from sortable.path import Path

def usage():
    print(__doc__)    

def copy_media(source, source_root, destination_root):
    m3u = M3U(source)

    print("Source root:", source_root)
    print("Destination root:", destination_root)
    total_size = 0
    total_items = 0
    for item in m3u:
        full_path = os.path.join(item.path, item.filename)
        print("")
        print("Starting:", str(full_path))
        if re.match(str(source_root), str(full_path)):
            p = Path(full_path)
            relative = p.to_relative(source_root)
            print("relative pre:", relative)
            sparent = p.parent()
            destination = os.path.join(destination_root, relative)
            dpath = Path(destination)
            dparent = dpath.parent()
            print("relative post:", relative)
            print(sparent)
            print(destination)

            if not os.path.exists(str(dparent)):
                os.makedirs(str(dparent))

            if not os.path.exists(destination):
                p.copy(destination)
            else:
                print("already have: %s" % destination)

            for option in os.listdir(str(sparent)):
                soption = os.path.join(str(sparent), option)
                spath = Path(soption)
                print(spath.type())
                if spath.type() != "Movie" and spath.type() != "Directory":
                    doption = os.path.join(str(dparent), option)
                    if not os.path.exists(doption):
                        print("copy here: %s, to %s" % (soption, doption))
                        shutil.copy(soption, doption)
                    
                

            print()

def main():
    #this is used to distinguish actual media from markers
    source_root = '/media/source/'

    destination_root = '/media/destination'

    #requires that at least one argument is passed in to the script itself
    #(through sys.argv)
    if len(sys.argv) > 1:
        helps = ['--help', 'help', '-h']
        for i in helps:
            if i in sys.argv:
                usage()
                exit()
        source = sys.argv[1]
        if len(sys.argv) > 2:
            source_root = sys.argv[2]
            destination_root = sys.argv[3]

        copy_media(source, source_root, destination_root)

    else:
        usage()
        exit()
        
if __name__ == '__main__':
    main()
