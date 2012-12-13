#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2012.12.06 04:07:39 
# License: MIT 

# Requires:
# medley

# Description:
# accept a source playlist and a source dir
# walk through the source dir (ignoring ignores)
# look for new items and add them in (ideally tagged correctly)

TODO:
Thoughts of incorporating this into M3U, Marks, Collection, Journal...
load a list into a Journal like element where all items can be indexed based on tags
then split them back out to individual playlists
or into a single playlist with tagged sections

cd /c/videos 
python /c/medley/scripts/update_playlist.py playlists/20121206-vinyl-toget.m3u .
"""

import os, sys, codecs
import re

from medley.marks import M3U
from moments.path import Path, check_ignore
from moments.timestamp import Timestamp

def usage():
    print __doc__

## #media_check = re.compile('.*\.flv$')
## media_check = re.compile('(.*\.flv$|.*\.mp4$|.*\.mp3$)')
## a = "1234.mp4"
## b = "5678.flv"
## c = "9012.mp3"
## media_check.search(a)
## media_check.search(b)

def add_new(source_list, source_dir, destination=None):
    ignores = ["classics", "misc", "other", "youtube-dl", "playlists"]

    media_check = re.compile('(.*\.flv$|.*\.mp4$|.*\.mp3$)')

    m3u = M3U(source_list)
    if os.path.isdir(source_dir):
        source_dir_path = Path(source_dir)
        subdirs = source_dir_path.load().directories
        #subdirs = os.listdir(source_dir)
        for subdir in subdirs:
            print ""
            print "SUBDIR: %s" % subdir
            if not check_ignore(str(subdir), ignores):
                for root,dirs,files in os.walk(unicode(subdir)):
                    for f in files:
                        #TODO:
                        #general function is_media(f)
                        #one place that looks for file types
                        #and can group based on type (sound, video, image)
                        #maybe part of path?
                        #already there?

                        media_file = os.path.abspath(os.path.join(root, f))
                        if media_check.search(f):
                            if not media_file in m3u:
                                m3u.append(media_file)
                                print "adding: %s" % media_file
                        else:
                            print "skipping: %s" % media_file

    print ""
    print ""
    #for item in m3u:
    #    print item
    if destination is None:
        source_list_path = Path(source_list)
        dest_name = Timestamp().compact(accuracy="day") + "-videos.m3u"
        destination = os.path.join(str(source_list_path.parent()), dest_name)
        
    print "Saving to: %s" % destination
    m3u.save(destination)

def main():
    #requires that at least one argument is passed in to the script itself
    #(through sys.argv)
    if len(sys.argv) > 1:
        helps = ['--help', 'help', '-h']
        for i in helps:
            if i in sys.argv:
                usage()
                exit()
        source_list = sys.argv[1]
        if len(sys.argv) > 2:
            source_dir = sys.argv[2]
        else:
            source_dir = None

        add_new(source_list, source_dir)

    else:
        usage()
        exit()
        
if __name__ == '__main__':
    main()
