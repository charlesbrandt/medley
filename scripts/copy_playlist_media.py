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
cd /c/medley/scripts
python copy_playlist_media.py /media/path/to.m3u 

useful to use:

afterwards to update the original playlist to the new location:
python /c/medley/scripts/filter_m3u_path.py /media/path/to.m3u /media/previous/base/:/media/new/base/
"""
import os, sys, codecs
import re, shutil

from medley.marks import M3U

from moments.path import Path

def usage():
    print __doc__    

def copy_media(source, source_root, destination_root):
    m3u = M3U(source)

    total_size = 0
    total_items = 0
    for item in m3u:
        if re.match(source_root, item):
            p = Path(item)
            relative = p.to_relative(source_root)
            sparent = p.parent()
            destination = os.path.join(destination_root, relative)
            dpath = Path(destination)
            dparent = dpath.parent()
            print relative
            print sparent
            print destination

            if not os.path.exists(str(dparent)):
                os.makedirs(str(dparent))

            if not os.path.exists(destination):
                p.copy(destination)
            else:
                print "already have: %s" % destination

            for option in os.listdir(str(sparent)):
                soption = os.path.join(str(sparent), option)
                spath = Path(soption)
                print spath.type()
                if spath.type() != "Movie" and spath.type() != "Directory":
                    doption = os.path.join(str(dparent), option)
                    if not os.path.exists(doption):
                        print "copy here: %s, to %s" % (soption, doption)
                        shutil.copy(soption, doption)
                    
                

            print

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
            destination = sys.argv[2]
        else:
            destination = None

        copy_media(source, source_root, destination_root)

    else:
        usage()
        exit()
        
if __name__ == '__main__':
    main()
