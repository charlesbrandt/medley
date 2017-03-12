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
from __future__ import print_function
import os, sys, codecs
import re

from medley.formats import M3U
from medley.helpers import load_json, get_media_properties
from medley.content import Content

from moments.path import Path, check_ignore

def usage():
    print(__doc__)    

def size_of_list(source, media_root=None, ignores=['/c/',]):
    """
    ignores are used to distinguish actual media from markers
    """
    items = []
    if re.search('.m3u', source):
        items = M3U(source)

    elif re.search('.json', source):
        loaded = load_json(source)

        #see if we have a dictionary or a list:
        if isinstance(loaded, list):
            #already have a list
            #clean it up
            for item in loaded:
                #these are usually content .json files:
                content = Content(item[0])
                #print content.media
                items.append(content.media[-1][0])
        elif isinstance(loaded, dict):
            #walk the tree to load each item individually
            #could call size_of_list() recursively
            pass

    total_size = 0
    total_items = 0
    #seconds?
    total_length = 0
    for item in items:
        check_item = False
        if media_root and re.match(media_root, item):
            check_item = True
        #elif not re.match(ignore, item):
        elif not check_ignore(item, ignores):
            check_item = True

        if check_item:
            p = Path(item)
            f = p.load()

            total_size += f.check_size()
            results = get_media_properties(item)
            print(results)
            total_length += results[1]
            total_items += 1
            #print item

    print("found %s matching items" % total_items)
    return total_size, total_length, total_items

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
        print(result)

    else:
        usage()
        exit()
        
if __name__ == '__main__':
    main()
