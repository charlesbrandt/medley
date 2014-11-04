#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2014.10.30 14:11:44 
# License: MIT 

# Requires:
# medley
# avconv

# Description:
# Scan the marks associated with a specified source content
# look for all marks with skip_start and matching skip_stop
# (could just look for 'skip' then skip to the next mark
# generate commands to avconv to handle those edits
# update mark times accordingly
# save as a new version

"""

import os, sys, codecs, re
import subprocess

from medley.helpers import find_json
from medley.content import Content

def usage():
    print __doc__
    
def handle_skips(source, destination):
    #source must have the corresponding suffix to use for output
    parts = source.split('.')
    source_prefix = '.'.join(parts[:-1])
    suffix = parts[-1]

    if not destination:
        destination = source_prefix + '.new'

    root = os.path.dirname(destination)
    print root
    
    jfile = find_json(source)
    print jfile
    content = Content(jfile)
    
    #using this for updating segments
    content_copy = Content(jfile)
    
    #print content.segments
    in_skip = False
    skip_start = ''
    keep_start = 0
    keep_end = None
    part = 0
    dest_parts = []
    #tailor this to the way you want to decide which segments to remove
    for segment in content.segments[:]:
        #I think we will actually need to extract the clips we want to keep
        #and then concatenate those together at the end
        #(and then update all of the timestamps)

        if re.search('skip', segment.title):
            duration = 0
            if segment.start == keep_start:
                #nothing to keep here... just update the keep_start and move on
                keep_start = segment.end.total_seconds()
                keep_end = None
            else:
                keep_end = segment.start.total_seconds()
                #we have a segment to keep...
                duration = keep_end - keep_start

                dest_part = "%s.part%03d.%s" % (destination, part, suffix)
                dest_parts.append(dest_part)
                
                print dest_part
                #extract it:
                command = "avconv -i %s -ss %s -t %s -vcodec copy -acodec copy %s" % (source, keep_start, duration, dest_part)
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print command
                #print process.communicate()[0]

                #update these values
                keep_start = segment.end.total_seconds()
                keep_end = None

            #make a copy of Content object
            #update the position for all subsequent segments and marks
            matched_current = False
            for copy_segment in content_copy.segments[:]:
                if (copy_segment.title == segment.title):
                    matched_current = True
                    content_copy.segments.remove(copy_segment)
                elif matched_current:
                    new_start = copy_segment.start.total_seconds() - duration
                    copy_segment.start.position = new_start * 1000
                    if copy_segment.end:
                        new_end = copy_segment.end.total_seconds() - duration
                        copy_segment.end.position = new_end * 1000
                    
            part += 1

    #now join all of the parts back together:

    #ffmpeg seems more versatile than avconv for joining files:
    #https://trac.ffmpeg.org/wiki/How%20to%20concatenate%20(join,%20merge)%20media%20files
    file_list = os.path.join(root, "temp.txt")
    f = codecs.open(file_list, 'w', encoding='utf-8')    
    for dest_part in dest_parts:
        f.write("file '" + dest_part + "'\n")
    f.close()
    final_dest = "%s.total.%s" % (destination, suffix)
    command = "ffmpeg -f concat -i %s -c copy %s" % (file_list, final_dest)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print command
    #print process.communicate()[0]
    #unfortunately, this creates a segmentation fault

    #update the new content's filename
    
    #save the new corresponding json file
    destination_json = destination + '.json'
    content_copy.save(destination_json)

        ## #this won't work, but need a way to check
        ## skip_found = False
        ## if re.search('skip', segment.title):
        ##     skip_found = True
        ##     #ok... we have a skip request...
        ##     #TODO:
        ##     #describe process
        ##     #ensure that we have both a start and end
        ##     # if end is none 
        ##     #  find end of the track, use that position (trim the end)
        ##     # all changes should be made to a temporary version
        ##     # both wav
        ##     # and json
        ##     # generate avconv command
        ##     # then adjust all subsequent segment times by the time being removed
        ##     # run avconv command
        ##     # save both
        ##     # use while loop to repeat until no skip requests found
        ##     # while skip_found:
        ##     #     (this is needed to get the latest version of segments)
            
            
        ##     print segment.title
        ##     print segment.start
        ##     print segment.end
        ##     #print segment.__dict__.keys()
        ##     print

        
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

    handle_skips(source, destination)

    #TODO:
    #handle 'extract' tags

    #TODO:
    #handle 'silence' tags (replace with silence)



    ## #to require that at least one argument is passed in to the script itself
    ## #(through sys.argv)
    ## #comment previous merge_logs call, then uncomment:
    ##     merge_logs(source, destination)

    ## else:
    ##     usage()
    ##     exit()

