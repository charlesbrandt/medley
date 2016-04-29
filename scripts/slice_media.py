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

see also medley.content.Content.split_media() methods

"""

import os, sys, codecs, re
import subprocess
from datetime import datetime

from medley.helpers import find_json, get_media_properties
from medley.content import Content
from moments.tag import to_tag

def usage():
    print __doc__


def make_destination(dest_prefix, part, extension, cur_tags=[]):
    main_title = '-'.join(cur_tags)
    title = to_tag(main_title)
    
    #dest_part = "%s%02d-%s.%s" % (destination, part, title, suffix)
    dest_part = "%s-%02d-%s.%s" % (dest_prefix, part, title, extension)
    #dest_part = "%s.part%03d.%s" % (destination, part, suffix)
    #force webm here
    #dest_part = "%s.part%03d.%s" % (destination, part, extension)

    #print dest_part
    return dest_part


def extract_segment(source, dest_part, keep_start, cur_duration, bitrate, extension):
    """
    source
    extension: for overriding the extension / file type
    keep_start: where to start
    segment: gives us the end
    bitrate
    part: for creating the filename
    """
    

    #extract it:

    #this one is good for keeping the format the same:
    #command = "avconv -i %s -ss %s -t %s -vcodec copy -acodec copy %s" % (source, keep_start, cur_duration, dest_part)

    #this will convert to webm for easier use in a browser:
    #but will also take longer
    command = "avconv -i %s -ss %s -t %s -f webm -c:v libvpx -qmin 0 -qmax 50 -crf 10 -b:v %s -threads 4 -acodec libvorbis %s" % (source, keep_start, cur_duration, bitrate, dest_part)
    #via: http://superuser.com/questions/556463/converting-video-to-webm-with-ffmpeg-avconv

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print command
    while process.poll() is None:
        #depending on which channel has output, can tailor that here
        l = process.stderr.readline()
        #l = process.stdout.readline()
        #print l

    #when process terminates, can finish printing the rest:
    #print process.stdout.read()

    

def slice_media(source, destination=None, keep_tags=[], skip_tags=[], duration=None, bitrate='6M', extension='webm'):
    """
    take a source (and optional destination)
    load and
    set up the other files that will be needed for the desired slice operation
    """
    #source must have the corresponding suffix to use for output
    print "STARTING: ", datetime.now()
    base = os.path.dirname(source)
    print base
    filename = os.path.basename(source)
    print filename

    edits_dir = os.path.join(base, "edits")
    if not os.path.exists(edits_dir):
        os.makedirs(edits_dir)

    print "EDITS DIR: ", edits_dir
    
    file_parts = filename.split('.')
    source_prefix = '.'.join(file_parts[:-1])
    suffix = file_parts[-1]

    if not destination:
        #destination = source_prefix + '.new'
        destination = source_prefix + ''

    destination = os.path.join(edits_dir, destination)
    print "DESTINATION: ", destination
    
    destination_json = destination + '.json'
    if os.path.exists(destination_json):
        #get rid of it...
        #don't want to load it 
        os.remove(destination_json)

    #final_dest = "%s.total.%s" % (destination, suffix)
    #using extension to override
    final_dest = "%s.total.%s" % (destination, extension)
    if os.path.exists(final_dest):
        #get rid of it...
        #don't want to load it 
        os.remove(final_dest)

    print "FINDING JSON FOR: %s" % source
    jfile = find_json(source, limit_by_name=False)
    print "JSON FILE:", jfile
    content = Content(jfile)
    #print content.debug()
    
    #using this for updating segments
    content_copy = Content(jfile)
    



    #print content.segments
    in_skip = False
    skip_start = ''
    #TODO:
    #initialize here so we can check what the last value was
    keep_match = False
    segment = None
    cur_tags = []
    
    keep_start = 0
    keep_end = None
    part = 0
    dest_parts = []
    #tailor this to the way you want to decide which segments to remove
    for segment in content.segments[:]:
        #we need to extract the clips we want to keep
        #and then concatenate those together at the end
        #(and then update all of the timestamps)

        #only one or the other should be used at a time

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

        if keep_match:
            #keep track of cur_tags
            title_parts = segment.title.split('. ')
            main_title = title_parts[-1]
            tags = main_title.split(', ')
            for tag in tags:
                if not re.search('\+', tag) and not tag in cur_tags:
                    cur_tags.append(tag)

        
        if not keep_match:
            #this is the cur_duration of all of the segments that we are keeping!!
            cur_duration = 0

            #TODO:
            ## if end is none 
            ## find end of the track, use that position (trim the end)
            if not segment.end:
                pass

            #check if there is anything that we've scanned previously
            #that we need to keep before skipping this segment
            
            if float(segment.start.total_seconds()) != float(keep_start):
                print "we have a segment to keep... %s != %s" % (segment.start.total_seconds(), keep_start)

                keep_end = segment.start.total_seconds()
                print keep_end
                cur_duration = keep_end - keep_start

                dest_part = make_destination(destination, part, extension, cur_tags)
                dest_parts.append(dest_part)

                #extract_segment(source, destination, extension, keep_start, cur_duration, bitrate, part, dest_parts)
                extract_segment(source, dest_part, keep_start, cur_duration, bitrate, extension)
                

            if segment.end:
                skip_duration = segment.end.total_seconds() - segment.start.total_seconds()
                #update these values
                keep_start = segment.end.total_seconds()
                
            keep_end = None
            
            #make a copy of Content object
            #update the position for all subsequent segments and marks
            matched_current = False
            for copy_segment in content_copy.segments[:]:
                #this only updates the segments... 
                #not the mark_list or the title_list
                copy_segment.json_source = destination_json
                copy_segment.filename = os.path.basename(final_dest)
                if (copy_segment.title == segment.title):
                    #print "Matched: ", copy_segment.title
                    matched_current = True
                    content_copy.segments.remove(copy_segment)
                elif matched_current:
                    #print "Updating: ", copy_segment.title, " Removing: ", skip_duration
                    #print "Original start: ", copy_segment.start.position
                    new_start = copy_segment.start.total_seconds() - skip_duration
                    copy_segment.start.position = new_start * 1000
                    #print "New start: ", copy_segment.start.position
                    if copy_segment.end:
                        new_end = copy_segment.end.total_seconds() - skip_duration
                        copy_segment.end.position = new_end * 1000

            #don't want to do this:
            #duration = duration - skip_duration
            
            print ""
            part += 1
            #reset these
            cur_tags = []


    if keep_match:
        #if the last segment was a keep_match,
        #make sure we extract the last one:


        if segment.end:
            keep_end = segment.end.total_seconds()
        else:
            keep_end = duration

        print keep_end
        cur_duration = keep_end - keep_start
            
        dest_part = make_destination(destination, part, extension, cur_tags)
        dest_parts.append(dest_part)

        extract_segment(source, dest_part, keep_start, cur_duration, bitrate, extension)
        #extract_segment(source, destination, extension, keep_start, cur_duration, bitrate, part, dest_parts)                


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

    properties = get_media_properties(source)
    duration = properties[1]
    bitrate = properties[2]
    bitstr = "%sk" % bitrate
    print bitstr
    #exit()

    #slice_media(source, destination, keep_tags=['\+'], bitrate='2M')
    #slice_media(source, destination, keep_tags=['\+'], bitrate='6M')
    slice_media(source, destination, keep_tags=['\+'], duration=duration, bitrate=bitstr)
    #slice_media(source, destination, keep_tags=['keep'])
    
    #TODO:
    #handle 'extract' tags

    #TODO:
    #handle 'silence' tags (replace with silence)


