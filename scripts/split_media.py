#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2015.01.06 13:12:55 
# License: MIT 

# Requires:
# medley
# avconv

# Description:
# similar to slice_media
# but instead of extracting skips
# this version only splits the file into the marked segements

"""

import os, sys, codecs, re
import subprocess

from moments.tag import to_tag

from medley.helpers import find_json, split
from medley.content import Content, Mark

def usage():
    print __doc__

def split(source, destination):
    """
    for similar functionality for importing into other scripts, see also:
    medley.content.Content.extract_segment
    """
    #source must have the corresponding suffix to use for output
    parts = source.split('.')
    source_prefix = '.'.join(parts[:-1])
    suffix = parts[-1]

    if not destination:
        destination = source_prefix + '.new'

    root = os.path.dirname(destination)
    print "ROOT:", root    
    
    jfile = find_json(source, limit_by_name=False, debug=True)
    print "json:", jfile
    content = Content(jfile)
    
    #using this for updating segments
    content_copy = Content(jfile)
    
    #print content.segments
    ## in_skip = False
    ## skip_start = ''
    ## keep_start = 0
    ## keep_end = None
    part = 1
    ## dest_parts = []

    find_end_command = "avconv -i %s 2>&1 | grep 'Duration' | awk '{print $2}' | sed s/,//" % (source)
    process = subprocess.Popen(find_end_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = process.communicate()[0].strip()
    mark = Mark()
    mark.from_time(result)
    
    print mark.total_seconds()
    media_end = ''

    created = []

    #tailor this to the way you want to decide which segments to remove
    for segment in content.segments[:]:
        #extract the clips

        keep_start = segment.start.total_seconds()
        if segment.end:
            keep_end = segment.end.total_seconds()
        else:
            keep_end = mark.total_seconds()
        #we have a segment to keep...
        duration = keep_end - keep_start
        title_parts = segment.title.split('. ')
        main_title = title_parts[-1].replace(', ', '-')
        title = to_tag(main_title)
        
        dest_part = "%s%02d-%s.%s" % (destination, part, title, suffix)

        command = "avconv -i %s -ss %s -t %s -vcodec copy -acodec copy %s" % (source, keep_start, duration, dest_part)
        print command
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        #print process.communicate()[0]

        created.append(dest_part)

        part += 1

    return created
    
        
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

    split(source, destination)


