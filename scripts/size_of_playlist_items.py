#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2013.06.05 21:46:45 
# License: MIT 

# Requires:
# moments

# Description:
go through all items in a playlist and determine the size the disk space that the items use

cd /c/medley/scripts
python size_of_playlist_items.py /media/path/to.m3u

"""
import os, sys, codecs
import re

from medley.marks import M3U

from moments.path import Path

def usage():
    print __doc__    

def size_of_list(source, media_root=None):
    #ignore is used to distinguish actual media from markers
    ignore = "/c/"
    
    m3u = M3U(source)

    total_size = 0
    total_items = 0
    for item in m3u:
        check_item = False
        if media_root and re.match(media_root, item):
            check_item = True
        elif not re.match(ignore, item):
            check_item = True

        if check_item:
            p = Path(item)
            f = p.load()

            total_size += f.check_size()
            total_items += 1
            #print item

    print "found %s matching items" % total_items
    return total_size

def main():
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
            media_root = sys.argv[2]
        else:
            media_root = None

        result = size_of_list(source, media_root)
        print result

    else:
        usage()
        exit()
        
if __name__ == '__main__':
    main()
