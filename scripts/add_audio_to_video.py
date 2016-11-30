#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2016.11.12 09:30:17 
# License: MIT 

# Requires:
# avconv

# Description:
Take an audio file and replace the existing audio on a video file with it

"""

import os, sys, codecs, re
import subprocess

def usage():
    print __doc__

def combine(video, audio, destination=None):
    """

    """
    if not destination:
        destination = video + ".combined"

    # is -c:v equivalent to -vcodec?
    #command = "avconv -i %s -i %s -c:v copy -c:a libvorbis %s" % (video, audio )
    
    command = "avconv -i %s -i %s -vcodec copy -acodec libvorbis -strict experimental -map 0:v:0 -map 1:a:0 %s" % (video, audio, destination)
    print command
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    #print process.communicate()[0]


        
if __name__ == '__main__':
    video = None
    audio = None
    destination = None
    if len(sys.argv) > 1:
        helps = ['--help', 'help', '-h']
        for i in helps:
            if i in sys.argv:
                usage()
                exit()
                
        video = sys.argv[1]
        audio = sys.argv[2]
        if len(sys.argv) > 3:
            destination = sys.argv[3]
        else:
            destination = None

    combine(video, audio, destination)


