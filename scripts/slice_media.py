#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2016.09.27 22:09:18 
# License: MIT 

# Requires:
# medley
# avconv

Original script moved in as part of medley core.
This is a wrapper / example for the main functionality.

see also medley.content.Content.split_media() methods

Warning: This does not work well with media stored in .iso files
The times marked with medley are often different than those that get extracted
it's best to note times on a single file instead of an iso


"""
from medley.helpers import get_media_properties
from medley.slice_media import slice_media

def usage():
    print __doc__
        
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

    properties = get_media_properties(source)
    duration = properties[1]
    bitrate = properties[2]
    bitstr = "%sk" % bitrate
    print bitstr
    #exit()

    slice_media(source, destination, keep_tags=['\+'], duration=duration, bitrate=bitstr)


