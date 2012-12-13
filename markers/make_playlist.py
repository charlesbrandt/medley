#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2012.09.27 18:55:35 
# License:  MIT 

# Description:
# generate markers playlists for incorporation into other playlists

"""

import os, sys, codecs, re

ROOT = "/c/medley/markers"

def usage():
    print __doc__

            
def add_markers(dest):
    global ROOT
    #Add in marker items to help with sorting
    dest.write("""#EXTINF:0,1.svg
%s/1.svg
#EXTINF:0,2.svg
%s/2.svg
#EXTINF:0,3.svg
%s/3.svg
#EXTINF:0,4.svg
%s/4.svg
""" % (ROOT, ROOT, ROOT, ROOT))

def print_m3u(items, dest_file="temp.m3u", append=False):
    if append:
        dest = open(dest_file, 'a')
    else:
        dest = open(dest_file, 'w')

    if not append:
        dest.write("#EXTM3U\n")
        add_markers(dest)

    counter = 10
    for item in items:
        name = str(item).split('/')[-1]
        dest.write("#EXTINF:%s,%s\n" % (counter, name))
        dest.write(item)
        dest.write('\n')
        counter += 1
        
        add_markers(dest)

    #if not append:
    #    add_markers(dest)

    dest.close()

if __name__ == '__main__':
    #root = '/c/medley/markers'
    root = ROOT
    all_items = os.listdir(root)
    items = []
    for i in all_items:
        if not re.match('^[0-9]*.svg', i) and re.search('.*\.svg$', i):
            items.append(os.path.join(root, i))

    print_m3u(items)
    
    

