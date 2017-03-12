#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2014.12.17 11:11:03 
# License: MIT 

# Requires:
medley

# Description:

Sometimes content is moved around.
Content objects stored in .json files may have old locations.
this is a helper to go through and update those

it might be possible to just use a global find and replace approach
but this should be more specific and easier to customize

TODO:
consider moving this to Content object itself, if it proves useful

seems to be as simple as loading and re-saving a content object...
not sure why some contexts are having difficulty
wrong drive_dir supplied?
"""
from __future__ import print_function

import os, sys, codecs, re

from medley.helpers import load_json, save_json
from medley.content import Content
from medley.playlist import Playlist

def usage():
    print(__doc__)
    
def update_jsons(source):
    """
    similar to, but different from medely.helpers.find_json

    check for existence of source moved out from here...
    must check!
    """
    
    json_check = re.compile('.*\.json$')    

    for root,dirs,files in os.walk(source):
        for f in files:
            current_file = os.path.join(root, f)
            if json_check.search(f):
                print()
                print(current_file)
                result = load_json(current_file)
                #if isinstance(result, dict) and result.has_key('segments'):
                if isinstance(result, dict) and 'media' in result:
                    content = Content(current_file)
                    print(content.drive_dir)
                    #for segment in content.segments:
                    #    print segment.json_source
                    #scan_content(content, cur_lists)
                    #all_contents[current_file] = content
                    #if f == "20120117.json":
                    content.save()

                else:
                    print("Skipping: %s... not a Content object" % current_file)

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

        ## if len(sys.argv) > 2:
        ##     tags = sys.argv[2]
        ## else:
        ##     tags = ''
        ##     usage()
        ##     exit()

        if os.path.exists(source):
            if not os.path.isdir(source):
                source = os.path.basedir(source)
        else:
            print("Couldn't find path: %s" % source)
            exit()


        update_jsons(source)


