#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2014.12.05 11:39:30 
# License: MIT 

# Requires:
# medley

# Description:
#
scan a given directory for all json content items (easy way to tell the difference from playlists?)

out of all main contents
scan for ones tagged 'verified' or 'on_list' (or ___?)
go through all sub contents
look for any tagged (list of approved tags)
skip any tagged (list of skip tags)
add anything else to a misc list

automatically group by the number of "+" elements in a tag
finally, if possible, use any previous list to apply an order 
(could either use the previous automatic playlist, or could use a manually specified source... input parameters could get tricky for that, but might be worth having)

see also:
/c/medley/scripts/update_playlist.py
/c/binaries/podcasts/beats_in_space/make_playlist.py
/c/medley/medley/helpers.py
/c/medley/scripts/copy_media.py
/c/medley/scripts/make_relative_playlist.py

python automatic_json_lists.py source_directory "tag list separated by spaces"
"""

import os, sys, codecs, re

from medley.helpers import load_json, save_json
from medley.content import Content
from medley.playlist import Playlist

def usage():
    print __doc__

def parse_tags(source):
    """
    extract any substring enclosed in parenthesis
    source should be a string
    
    normally would use something like json for this
    but I would like to make it easy to specify these tags and their groups
    manually (via text box or command line argument)

    http://stackoverflow.com/questions/1651487/python-parsing-bracketed-blocks
    """
    unmatched_count = 0
    start_pos = 0
    opened = False
    open_pos = 0
    cur_pos = 0

    finished = []
    segments = []

    for character in source:
        #scan for mismatched parenthesis:
        if character == '(':
            unmatched_count += 1
            if not opened:
                open_pos = cur_pos
            opened = True

        if character == ')':
            unmatched_count -= 1

        if opened and unmatched_count == 0:
            clean = source[start_pos:open_pos]
            clean = clean.strip()
            if clean:
                finished.extend(clean.split())

            segment = source[open_pos:cur_pos+1]
            #segments.append(segment)
            
            #get rid of bounding parentheses:
            pruned = segment[1:-1]
            group = pruned.split()
            finished.append(group)

            opened = False
            start_pos = cur_pos+1
                
        cur_pos += 1

    assert unmatched_count == 0

    if start_pos != cur_pos:
        #get anything that was left over here
        remainder = source[start_pos:cur_pos].strip()
        finished.extend(remainder.split())
    
    ## #now check on recursion:
    ## for item in segments:
    ##     #get rid of bounding parentheses:
    ##     pruned = item[1:-1]
    ##     if recurse:
    ##         results = parse_tags(pruned, recurse)
    ##         finished.expand(results)
    ##     else:
    ##         finished.append(pruned.strip())
            
    return finished
    
def make_empty_lists(tags):
    """
    make a common structure to hold lists in
    useful when scanning and merging multiple collections

    if tags are surrounded by '()', those tags all point to the same list:

    for example:
    a = []
    b = []
    z = {"a": a, "b":b, "c":a}
    z['a'].append("q")
    z['b'].append("r")
    z['c'].append("s")
    print z

    
    """
    all_lists = {}

    #these are the first ones listed in sub groups of tags
    main_tags = []

    #if no nested groups of tags, this will work:
    ## all_tags = tags.split()
    ## for tag in all_tags:
    ##     all_lists[tag] = []

    all_tags = parse_tags(tags)
    for tag in all_tags:
        if isinstance(tag, list):
            main_tags.append(tag[0])
            shared_list = []
            for sub_tag in tag:
                all_lists[sub_tag] = shared_list
        else:
            main_tags.append(tag)
            all_lists[tag] = []

    #pick up unmatched tags that have a '+' in any tag:
    all_lists['good'] = []
    main_tags.append('good')
    #for everything else:
    all_lists['misc'] = []
    main_tags.append('misc')

    return all_lists, main_tags

def find_verified(content, root=True):
    """
    recursive helper to find all segments with appropriate tags
    """
    verified = []
    
    matched = False
    all_status = []

    if ("verified" == content.status) or ("on_list" == content.status):
        verified.append(content)
        matched = True
    else:
        #print "Nothing matched: %s" % content.status
        if not content.status in all_status:
            all_status.append(content.status)

        for segment in content.segments:
            result = find_verified(segment, False)
            verified.extend(result)

    if not matched and root:
        print "Warning: no valid status (%s) for content: %s" % (all_status, content.json_source)
        
    return verified

def scan_content(content, cur_lists):
    """
    take a content that has been loaded
    see if it has been verified or on a list
    add segments if so
    """

    #even if there are multiple tags for one list,
    #they should all have a separate key that was created in make_empty_lists()
    all_tags = cur_lists.keys()
    
    verified = find_verified(content)

    #print
    #print verified
    #print len(verified)

    #could customize these:
    skip_tags = [ 'skip', 'meh', 'blah', 'bad' ]

    #TODO:
    #for some content without titles, tags are sometimes placed in title
    #could scan titles for tags to place in appropriate list
    
    for item in verified:
        #now scan all segments in item for valid playlist tags...
        #do not recurse here! one level is sufficient now
        for segment in item.segments:
            skip = False
            for skip_tag in skip_tags:
                if skip_tag in segment.tags:
                    skip = True

            if not skip and segment.tags:
                matched = False

                #add items to the appropriate list based on tags
                for tag in all_tags:
                    if tag in segment.tags:
                        cur_lists[tag].append(segment)
                        matched = True
                        
                #special cases:        
                if not matched:
                    for tag in segment.tags:
                        #sometimes 'skip' may be in the tag... e.g. "skip?"
                        if re.search("skip", tag):
                            matched = True
                        elif re.search("\+", tag):
                            cur_lists['good'].append(segment)
                            matched = True
                
                if not matched:                    
                    print "Couldn't match: ", segment.tags

                    #could append to misc, if wanted
                    cur_lists['misc'].append(segment)
                    
            #print segment.status

    print
    #print content.debug(recurse=False)

def find_all_jsons(source, cur_lists, type=None):
    """
    look in the specified source directory
    (or the parent directory, if source is a file)
    find all json files
    
    if type is specified, can load and filter them accordingly

    similar to, but different from medely.helpers.find_json

    check for existence of source moved out from here...
    must check!
    """
    
    json_check = re.compile('.*\.json$')    

    for root,dirs,files in os.walk(source):
        for f in files:
            current_file = os.path.join(root, f)
            if json_check.search(f):
                #print current_file
                result = load_json(current_file)
                if isinstance(result, dict) and result.has_key('segments'):
                    #going to assume this is a content object...
                    #reload it that way:
                    content = Content(current_file)
                    scan_content(content, cur_lists)
                else:
                    print "Skipping: %s... not a Content object" % current_file

                #print result
                #print 
                #print 

        
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
            tags = sys.argv[2]
        else:
            tags = ''
            usage()
            exit()

        if os.path.exists(source):
            if not os.path.isdir(source):
                source = os.path.basedir(source)
        else:
            print "Couldn't find path: %s" % source
            exit()

        #TODO
        #would be nice to have a config file
        #for scanning multiple source directories

        #TODO:
        #then merge all of those lists together into combined versions of each
        #also [2014.12.08 18:50:00]
        #not sure that we really want to do that...
        #could get very big an unweildy
        #should instead, come up with ways to skim the cream of the crop

        cur_lists, main_tags = make_empty_lists(tags)
        print main_tags
        
        find_all_jsons(source, cur_lists)


        source_name = os.path.basename(source)
        lists_index = { 'source':'', 'name':source_name, 'children':[] }
        #lists_index = { 'source':'', 'name':source_dirname, 'children':[] }

        #save all lists:
        for tag in main_tags:
            cur_list = cur_lists[tag]
            if len(cur_list):
                pl = Playlist(cur_list)
                name = "%s.json" % tag
                dest = os.path.join(source, name)
                if os.path.exists(dest):
                    print "WARNING: path exists! ", dest

                #TODO:
                #before applying order of previous list
                #first sort by the number of "+" tags
                #that way new items show up sorted by rating

                #TODO:
                #check for existing / previous playlists
                #apply the order of those lists to newly generated list
                #anything new to the list should be added to the top
                #anything on old list that is not on new list should be kept off

                #TODO:
                #consider saving everything to a subdirectory with today's date
                #that way changes can be tracked more easily
                #(or could just rely on version control for that too)

                print "saving to: ", dest
                pl.save(dest)
                lists_index['children'].append( { 'source':dest, 'name':tag, 'children':[] } )


        index_name = source_name + '.json'
        index_dest = os.path.join(source, index_name)
        print "saving index to: %s" % index_dest
        save_json(index_dest, lists_index)



        #TODO:
        #handle a list for all top level content items ('everything')
        #although this is often handled (and customized)
        #when downloading and initially scanning / adding contents
        
        #print parse_tags("tag1 tag2 (group1 group2 group3) tag3 (groupx (groupy) groupz) tag4")
        
    else:
        usage()
        exit()

