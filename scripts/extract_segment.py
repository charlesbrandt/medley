#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# License: MIT 

# Requires:
#
# ffmpeg / avconv

# Description:
#
this functionality is also a method on Content objects
adapted from split_media script
"""
import argparse
import os
import sys
import codecs
import re
import subprocess


def from_hms(hours=0, minutes=0, seconds=0):
    """
    adapted from medley.content
    
    opposite of as_hms
    take hours, minutes, and seconds

    automatically set our local ms / position attribute ???
    """
    total_minutes = float(hours) * 60 + float(minutes)
    total_seconds = total_minutes * 60 + float(seconds)
    return total_seconds


def extract_segment(args):
    if re.search(':', args.start):
        parts = args.start.split(':')
        if len(parts) == 3:
            start_seconds = from_hms(parts[0], parts[1], parts[2])
        elif len(parts) == 2:
            start_seconds = from_hms(minutes=parts[0], seconds=parts[1])
        else:
            raise(ValueError, "Unknown time format (start)")

    start_str = '.'.join(parts)

    if re.search(':', args.end):
        parts = args.end.split(':')
        if len(parts) == 3:
            end_seconds = from_hms(parts[0], parts[1], parts[2])
        elif len(parts) == 2:
            end_seconds = from_hms(minutes=parts[0], seconds=parts[1])
        else:
            raise(ValueError, "Unknown time format (end)")

    end_str = '.'.join(parts)

    parts = args.destination.split('.')

    dest = '.'.join(parts[:-1]) + '-' + start_str + '-' + end_str + '.' + parts[-1]

    print(start_seconds, end_seconds)

    duration = end_seconds - start_seconds


    #works, but distorted
    command = "ffmpeg -ss %s -t %s -i %s -vcodec copy -acodec copy -preset veryslow %s" % (start_seconds, duration, args.source, dest)

    #this one didn't work
    #command = "ffmpeg -ss %s -to %s -i %s -vcodec copy -acodec copy -preset veryslow %s" % (start_seconds, end_seconds, args.source, args.destination)
    print(command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    print(process.communicate()[0])


    

    
if __name__ == '__main__':
    source = None
    destination = None
    
    #https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description='extract a clip from media')
    parser.add_argument('-s', '--start',
                        help='start of the clip')
    parser.add_argument('-e', '--end',
                        help='end of the clip')
    parser.add_argument('source')
    parser.add_argument('destination', default="output.mp4")

    args = parser.parse_args()
    parser.print_help()

    print(args)
    #print(args.accumulate(args.integers))

    extract_segment(args)

