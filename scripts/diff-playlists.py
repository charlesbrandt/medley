#!/usr/bin/env python
"""
# By: Charles Brandt [charlesbrandt at gmail dot com]
# On: *2013.04.11 18:30:13 
# License: MIT

# Requires:
medley

# Description:

take 2 m3u and report similarities
can then generate new lists based on what set you want

based off of very old script at:
/c/alpha/player/diff-playlists.py

"""
import os, sys, codecs
import re

from medley import marks

def usage():
    print __doc__

def diff_playlists(fpath1, fpath2):
    """
    take two file paths
    create 2 osbrowser nodes that represent playlists,
    then diff those 2 playlists
    """


    p1 = marks.M3U(fpath1)
    p2 = marks.M3U(fpath2)


    cur_pos = 0

    matches = []

    p1_only = []
    p2_only = []
    both = []
    
    for cur_opt in p1:
        match = False
        for location in p2:
            if location == cur_opt:
                match = True
                matches.append([location, cur_pos, p2.index(location)])
                both.append(location)
        if not match:
            if cur_opt in p1_only:
                print "P1 DUPE!!!: %s" % cur_opt
            else:
                p1_only.append(cur_opt)
        cur_pos += 1

    for cur_opt in p2:
        if not cur_opt in both:
            if cur_opt in p2_only:
                print "P2 DUPE!!!: %s" % cur_opt
            else:
                p2_only.append(cur_opt)



    print "BOTH: %s" % both
    print ""

    print "P2 ONLY: %s" % p2_only
    print ""

    print "P1 ONLY: %s" % p1_only
    print ""

    print "BOTH: %s, P1 ONLY: %s, P2 ONLY: %s" % (len(both), len(p1_only), len(p2_only))
    
    #can save here, if needed:
    destination = "temp.m3u"
    result = marks.M3U()
    for item in p1:
        if (re.search("mp4", item) or re.search("wmv", item)):
            if item in p1_only:
                result.append(item)
            else:
                #must have been a dupe...
                pass
        else:
            #for everything else (list structural elements)
            #just append them
            result.append(item)
    result.save(destination, verify=False)

def main():
    if len (sys.argv) > 1:
        if sys.argv[1] in ['--help','help']:
            usage()
        f1 = sys.argv[1]
        f2 = sys.argv[2]

        diff_playlists(f1, f2)

    else:
        usage()
        exit()
                
    
if __name__ == '__main__':
    main()

