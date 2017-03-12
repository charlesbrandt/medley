"""
helpful when the media of a playlist changes location
this version will rename the playlist with today's date
and automatically save it in the source directory

ex:
python filter_m3u_path.py /c/music/playlists/20120122-little_white_earbuds.m3u ../../binaries/podcasts/little_white_earbuds/:

last option is the translate argument with format of pre:post
"""
from __future__ import print_function
from builtins import str
import os, sys, re

from moments.journal import Journal
from moments.path import Path
from moments.timestamp import Timestamp

#see also:
#from copy_media import make_destination

if len(sys.argv) > 1:
    source_name = sys.argv[1]
    if len(sys.argv) > 2:
        translate = sys.argv[2]
    else:
        translate = None

    if translate is not None:
        (pre, post) = translate.split(':')
        matches = [ pre ]
    else:
        #can manually define here
        #(pre, post) = ('/c/binaries', '')
        ## matches = [ '/first/path/to/replace/', '/second/path/to/replace/' ]
        matches = ['/c/binaries', ]
        post = ''
    
    #for arg in sys.argv[1:]:

    # make new destination based on source
    now = Timestamp()
    spath = Path(source_name)
    parent = spath.parent()
    parts = spath.filename.split('-')
    new_parts = [ now.compact(accuracy="day") ]
    new_parts.extend(parts[1:])
    new_parts.insert(-1, "filtered")
    new_name = "-".join(new_parts)
    output = os.path.join(str(parent), new_name)
    print(output)
    #output = 'temp.m3u'

    source = file(source_name)
    destination = file(output, 'w')

    count = 0
    for line in source.readlines():
        for m in matches:
            if re.search(m, line):
                parts = line.split(m)
                line = post + parts[1]
                count += 1
                
        destination.write(line)
    print("%s updated from: %s" % (count, source_name))
    print("and saved to: %s" % (output))
    source.close()
    destination.close()
