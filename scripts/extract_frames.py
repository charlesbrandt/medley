#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2017.10.31 15:25:56 
# License: MIT 

# Requires:
#

# Description:
#

see also:
/c/movies/ffmpeg-avconv-commands.txt

"""
from __future__ import print_function

import os, sys, codecs, subprocess

from medley.helpers import find_json, get_media_properties
from medley.content import Content, Mark

from moments.path import Path

def usage():
    print(__doc__)


def extract_frame(source, ms):
    position = Mark(position=ms)
    parent_path = Path(source).parent()
    destination_file = "%s.jpg" % (position.position)
    dest_path = os.path.join(str(parent_path), destination_file)
    if not os.path.exists(dest_path):

        command1 = "ffmpeg -ss %s -i %s -vframes 1 -q:v 2 %s" % (position.as_time(), source, dest_path)
        print(command1)
        #print(os.cwd())
        process = subprocess.Popen(command1, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        #output = process.communicate()[0]
        output = process.communicate()[1]
    else:
        print("frame %s already exists; skipping" % destination_file)
    

def extract_frames_range(source, start, end, total, keep=False):
    """
    automatically extract a certain number of frames
    equally spaced
    based on the range specified

    keep them in a temp directory for eventual purge, as needed
    (garbage collection)
    """
    diff = end - start
    increment = diff / total
    count = 0
    position = start
    while count < total:
        print("extracting: ", position)
        position += increment
        extract_frame(source, position)
        count += 1

def extract_frames(source):
    #if source is not a directory
    #look in directory for content json
    #load json
    #if segments
    # find start for all segments
    # if frame file already exists, skip it
    # else:
    #  extract frame with ffmpeg
    #  ffmpeg -ss 00:00:34 -i [source] -vframes 1 -q:v 2 00034.jpg
    # return a dict with segment details + image source for segment
    default_json = find_json(source)
    print(default_json)
    
    content = Content(default_json)
    print(content.segments)
    for segment in content.segments:
        #do segments only resolve down to seconds?
        print(segment.title, segment.start.position)
        extract_frame(source, segment.start.position)
            
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

    print("(dimensions, seconds, bitrate)")
    print(get_media_properties(source))
    #extract_frames(source)
    extract_frames_range(source, 2042931, 2044760, 40)

