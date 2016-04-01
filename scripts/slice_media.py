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


def slice_media(source, destination=None, keep_tags=[], skip_tags=[]):
    """
    take a source (and optional destination)
    load and
    set up the other files that will be needed for the desired slice operation
    """
    #source must have the corresponding suffix to use for output
    parts = source.split('.')
    source_prefix = '.'.join(parts[:-1])
    suffix = parts[-1]

    if not destination:
        destination = source_prefix + '.new'
    
    destination_json = destination + '.json'
    if os.path.exists(destination_json):
        #get rid of it...
        #don't want to load it 
        os.remove(destination_json)

    final_dest = "%s.total.%s" % (destination, suffix)
    if os.path.exists(final_dest):
        #get rid of it...
        #don't want to load it 
        os.remove(final_dest)

    print "finding json for: %s" % source
    jfile = find_json(source, limit_by_name=False)
    print "json file:", jfile
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

        if keep_tags:
            keep_match = False
            for option in keep_tags:
                if re.search(option, segment.title):
                    keep_match = True
                    
        elif skip_tags:
            keep_match = True
            for option in skip_tags:
                if re.search(option, segment.title):
                    keep_match = False
        
        if not keep_match:
            #this is the duration of all of the segments that we are keeping!!
            duration = 0

            #TODO:
            ## if end is none 
            ## find end of the track, use that position (trim the end)
            if not segment.end:
                pass

            #check if there is anything that we've scanned previously
            #that we need to keep before skipping this segment
            
            if float(segment.start.total_seconds()) == float(keep_start):
                #nothing to keep here... just update the keep_start and move on
                if segment.end:
                    keep_start = segment.end.total_seconds()
                    keep_end = None
            else:
                print "we have a segment to keep... %s != %s" % (segment.start.total_seconds(), keep_start)

                keep_end = segment.start.total_seconds()
                print keep_end
                duration = keep_end - keep_start

                dest_part = "%s.part%03d.%s" % (destination, part, suffix)
                dest_parts.append(dest_part)
                
                print dest_part
                #extract it:
                command = "avconv -i %s -ss %s -t %s -vcodec copy -acodec copy %s" % (source, keep_start, duration, dest_part)
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print command
                while process.poll() is None:
                    #depending on which channel has output, can tailor that here
                    l = process.stderr.readline()
                    #l = process.stdout.readline()
                    #print l

                #when process terminates, can finish printing the rest:
                #print process.stdout.read()

                
                #update these values
                keep_start = segment.end.total_seconds()
                keep_end = None

            if segment.end:
                skip_duration = segment.end.total_seconds() - segment.start.total_seconds()
            
            #make a copy of Content object
            #update the position for all subsequent segments and marks
            matched_current = False
            for copy_segment in content_copy.segments[:]:
                #this only updates the segments... 
                #not the mark_list or the title_list
                copy_segment.json_source = destination_json
                copy_segment.filename = os.path.basename(final_dest)
                if (copy_segment.title == segment.title):
                    print "Matched: ", copy_segment.title
                    matched_current = True
                    content_copy.segments.remove(copy_segment)
                elif matched_current:
                    print "Updating: ", copy_segment.title, " Removing: ", skip_duration
                    print "Original start: ", copy_segment.start.position
                    new_start = copy_segment.start.total_seconds() - skip_duration
                    copy_segment.start.position = new_start * 1000
                    print "New start: ", copy_segment.start.position
                    if copy_segment.end:
                        new_end = copy_segment.end.total_seconds() - skip_duration
                        copy_segment.end.position = new_end * 1000

            print ""
            part += 1




    #now join all of the parts back together:

    #update the new content's filename
    content_copy.filename = os.path.basename(final_dest)
    content_copy.media = [final_dest]
    content_copy.split_segments()
    #save the new corresponding json file
    content_copy.save(destination_json)

    print "All dest parts: ", dest_parts

    #ffmpeg seems more versatile than avconv for joining files:
    #https://trac.ffmpeg.org/wiki/How%20to%20concatenate%20(join,%20merge)%20media%20files
    root = os.path.dirname(destination)
    print root
    file_list = os.path.join(root, "temp.txt")
    f = codecs.open(file_list, 'w', encoding='utf-8')    
    for dest_part in dest_parts:
        f.write("file '" + dest_part + "'\n")
    f.close()
    command = "ffmpeg -f concat -i %s -c copy %s" % (file_list, final_dest)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print process.communicate()[0]
    #unfortunately, this creates a segmentation fault
    #Segmentation fault (core dumped)
    #this was caused by no files being listed in temp.txt
    print

    ## file_list = ''
    ## for dest_part in dest_parts:
    ##     file_list += dest_part + '\|'

    ## #get rid of last '|'
    ## file_list = file_list[:-2]
    ## print file_list

    ## command = "avconv -i concat:%s -codec copy %s" % (file_list, final_dest)
    ## process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print command
    
    
        
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

    #handle_skips(source, destination)
    #handle_keeps(source, destination)
    slice_media(source, destination, keep_tags=['\+'])
    
    #TODO:
    #handle 'extract' tags

    #TODO:
    #handle 'silence' tags (replace with silence)


