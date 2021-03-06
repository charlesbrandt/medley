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

Warning: This does not work well with media stored in .iso files
The times marked with medley are often different than those that get extracted
it's best to note times on a single file instead of an iso


"""
from __future__ import print_function

import os, sys, codecs, re
import subprocess
from datetime import datetime

from medley.helpers import find_json, get_media_properties
from medley.content import Content
from moments.tag import to_tag

def usage():
    print(__doc__)


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
    print(command)
    while process.poll() is None:
        #depending on which channel has output, can tailor that here
        l = process.stderr.readline()
        #l = process.stdout.readline()
        #print l

    #when process terminates, can finish printing the rest:
    #print process.stdout.read()


def extract_audio(source, destination, keep_start, cur_duration):
    """
    source
    keep_start: where to start
    """
    #-vn (output)
    #       Disable video recording.

    #use:
    #avconv -codecs
    # to see a list of codecs availabe if copy is not preferred

    #command = "avconv -i %s -ss %s -t %s -vn -acodec copy %s" % (source, keep_start, cur_duration, destination)
    #wav?
    #multiple channels (more than 2)
    #command = "avconv -i %s -ss %s -t %s -vn -acodec pcm_s16le %s" % (source, keep_start, cur_duration, destination)
    command = "avconv -i %s -ss %s -t %s -vn -ac 2 %s" % (source, keep_start, cur_duration, destination)

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(command)
    while process.poll() is None:
        l = process.stderr.readline()

def look_for_keeps(content, keep_tags, skip_tags):
    """
    depending on if keep_tags is sent
    or if skip_tags is sent
    will determine if the process is additive (add all keep_tags)
    or subtractive (ignore all skip_tags)
    """
    keeps = []

    #only one or the other (keep_tags vs skip_tags) should be used at a time
    if keep_tags:
        for segment in content.segments[:]:
            for option in keep_tags:
                if re.search(option, segment.title):
                    keeps.append(segment)

    elif skip_tags:
        for segment in content.segments[:]:
            keep_match = True
            for option in skip_tags:
                if re.search(option, segment.title):
                    keep_match = False
            #if checked everything and no match, must be a keeper
            if keep_match:
                keeps.append(segment)

    return keeps

def check_segment_end(segment, duration):
    """
    not all segments have an end set...
    helper to check for that without concern

    duration should be passed in to handle no segment end
    """
    end = duration
    #TODO: What about no end on segment?
    # get end of content (total length)
    if segment.end:
        end = segment.end.total_seconds()
        

    return end

def make_segment_groups(keeps, make_separate, duration):
    #depending on make_separate
    #if true, we want to create every keep segment individually
    #if not, we want to try to combine adjacent segments to minimize jump cuts

    #groups is always a list of lists 
    groups = []
    if make_separate:
        for item in keeps:
            groups.append( [ item, ] )
    else:
        cur_group = [ keeps[0] ]

        previous_end = check_segment_end(keeps[0], duration)

        for item in keeps[1:]:
            if item.start.total_seconds() == previous_end:
                cur_group.append( item )
            else:
                groups.append(cur_group)
                cur_group = [ item, ]

            previous_end = check_segment_end(item, duration)

    return groups    

def extract_group(group, source, destination, extension, bitrate, duration, offset=0, drift=1, audio_only=False):
    """
    take a list of one or more content.segments
    figure out the start and end
    figure out the corresponding tags
    do the extract
    """
    #extract the group:
    cur_duration = 0
    cur_tags = []
    part = None
    keep_start = None
    keep_end = None

    for segment in group:
        #check positions
        cur_start_adjusted = segment.start.total_seconds() * drift + offset
        if keep_start is None:
            keep_start = cur_start_adjusted
        #usually segments should be in order, but just in case:
        elif keep_start > cur_start_adjusted:
            keep_start = cur_start_adjusted

        cur_end_adjusted = check_segment_end(segment, duration) * drift + offset
        if keep_end is None:
            keep_end = cur_end_adjusted
        #usually segments should be in order, but just in case:
        elif keep_end < cur_end_adjusted:
            keep_end = cur_end_adjusted


        #update tags:
        title_parts = segment.title.split('. ')
        if part is None:
            part = int(title_parts[0])
        main_title = title_parts[-1]
        tags = main_title.split(', ')
        for tag in tags:
            if not re.search('\+', tag) and not tag in cur_tags:
                cur_tags.append(tag)

    cur_duration = keep_end - keep_start

    #print "AUDIO ONLY:", audio_only
    if audio_only:
        dest_part = make_destination(destination, part, "wav", cur_tags)
        extract_audio(source, dest_part, keep_start, cur_duration)

    else:
        dest_part = make_destination(destination, part, extension, cur_tags)

        extract_segment(source, dest_part, keep_start, cur_duration, bitrate, extension)

    return dest_part


def slice_media(source, destination=None, keep_tags=[], skip_tags=[], duration=None, bitrate='6M', extension='webm', make_separate=True, offset=0, drift=1, audio_only=False):
    """
    take a source (and optional destination)
    load and set up the other files 
    that will be needed for the desired slice operation

    if make_separate is True, adjacent 'keep' clips won't be extracted together
    this may cause rough transitions between clips when re-joined later
    """
    #source must have the corresponding suffix to use for output
    print("STARTING: ", datetime.now())
    base = os.path.dirname(source)
    print("Path: ", base)
    filename = os.path.basename(source)
    print("Filename: ", filename)

    edits_dir = os.path.join(base, "edits")
    if not os.path.exists(edits_dir):
        os.makedirs(edits_dir)

    print("EDITS DIR: ", edits_dir)
    
    file_parts = filename.split('.')
    source_filename_prefix = '.'.join(file_parts[:-1])
    suffix = file_parts[-1]

    if not destination:
        #destination = source_filename_prefix + '.new'
        destination = source_filename_prefix + ''

    destination = os.path.join(edits_dir, destination)
    print("DESTINATION: ", destination)
    
    destination_json = destination + '.json'
    if os.path.exists(destination_json):
        #get rid of it...
        #don't want to load it
        print("removing existing json to start fresh: ", destination_json)
        os.remove(destination_json)

    #final_dest = "%s.total.%s" % (destination, suffix)
    #using extension to override
    final_dest = "%s.total.%s" % (destination, extension)
    if os.path.exists(final_dest):
        #get rid of it...
        #don't want to load it 
        print("removing existing destinatino to start fresh: ", final_dest)
        os.remove(final_dest)

    print("FINDING JSON FOR: %s" % source)
    jfile = find_json(source, limit_by_name=False)
    print("JSON FILE:", jfile)

    content = Content(jfile)
    #print content.debug()
    
    #using this for updating segments
    content_copy = Content(jfile)
    

    #keeps = process_segments(content, keep_tags, skip_tags, content_copy, destination, destination_json, final_dest, make_separate, extension)

    dest_parts = []

    #depends on keep_tags or skip_tags, whichever one (and only one) is sent
    keeps = look_for_keeps(content, keep_tags, skip_tags)

    if keeps:
        groups = make_segment_groups(keeps, make_separate, duration)
        #now we know how things are grouped (even if everything is separate)
        

        for group in groups:
            dest_part = extract_group(group, source, destination, extension, bitrate, duration, offset, drift, audio_only=audio_only)

            dest_parts.append(dest_part)
    else:
        print("Nothing found to keep: %s" % keeps)


    #TODO:
    #could generate a corresponding content.json file 
    #for each exported segment based on the groups
    #(not necessary when make_separate == True)

    
    # now go through and update the content meta data
    # go through and create an updated content.json based on what was kept

    print(keeps)

    cur_pos = 0
    skip_duration = 0

    #assuming all segments in keep are still in the right order
    for segment in keeps:
        if cur_pos != segment.start.total_seconds():
            skip_duration += segment.start.total_seconds() - cur_pos

        cur_pos = check_segment_end(segment, duration)

        #update the segment
        new_start = segment.start.total_seconds() - skip_duration
        segment.start.position = new_start * 1000
        #print "New start: ", copy_segment.start.position
        if segment.end:
            new_end = segment.end.total_seconds() - skip_duration
            segment.end.position = new_end * 1000

        

    content_copy.segments = keeps



    #now join all of the parts back together:

    #update the new content's filename
    content_copy.filename = os.path.basename(final_dest)
    content_copy.media = [final_dest]
    content_copy.split_segments()
    #save the new corresponding json file
    content_copy.save(destination_json)

    print("All dest parts: ", dest_parts)

    #ffmpeg seems more versatile than avconv for joining files:
    #https://trac.ffmpeg.org/wiki/How%20to%20concatenate%20(join,%20merge)%20media%20files
    root = os.path.dirname(destination)
    print(root)
    file_list = os.path.join(root, "temp.txt")
    f = codecs.open(file_list, 'w', encoding='utf-8')    
    for dest_part in dest_parts:
        f.write("file '" + dest_part + "'\n")
    f.close()
    command = "ffmpeg -f concat -i %s -c copy %s" % (file_list, final_dest)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(process.communicate()[0])
    #unfortunately, this creates a segmentation fault
    #Segmentation fault (core dumped)
    #this was caused by no files being listed in temp.txt
    print()

    ## file_list = ''
    ## for dest_part in dest_parts:
    ##     file_list += dest_part + '\|'

    ## #get rid of last '|'
    ## file_list = file_list[:-2]
    ## print file_list

    ## command = "avconv -i concat:%s -codec copy %s" % (file_list, final_dest)
    ## process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(command)
    
    
        
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
    print(bitstr)
    #exit()

    #slice_media(source, destination, keep_tags=['\+'], bitrate='2M')
    #slice_media(source, destination, keep_tags=['\+'], bitrate='6M')
    slice_media(source, destination, keep_tags=['\+'], duration=duration, bitrate=bitstr)
    #slice_media(source, destination, keep_tags=['keep'])
    
    #TODO:
    #handle 'extract' tags

    #TODO:
    #handle 'silence' tags (replace with silence)


