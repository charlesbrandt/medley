import sys, os, codecs

from medley.marks import Marks
#import beats_in_space 

import logging
#http://docs.python.org/howto/logging.html#logging-basic-tutorial
#logging.basicConfig(format='%(message)s', level=logging.DEBUG)
logging.basicConfig(format='%(message)s', level=logging.INFO)

#print "reload(beats_in_space)"

#bis = beats_in_space.BeatsInSpace()

if len(sys.argv) > 1:
    source = sys.argv[1]
    if len(sys.argv) > 2:
        destination = sys.argv[2]
    else:
        destination = "temp.m3u"
else:
    source = "temp.mpb"
        
#from_mortplayer_original(source)

#update_locations(source)
#find_bookmarks(source)
#check_bookmark_availability(source)
#find_pluses(source)
#bis.merge_all_bookmarks_with_tracks()

f_marks = {}
marks = Marks(source)
marks.from_mortplayer()
marks.update_locations('/mnt/sdcard/external_sd/', '/c/')
#print marks
#marks.group_marks_by_file(f_marks)
#for key in f_marks.keys():
#    print key
#    print f_marks[key]

marks.to_m3u(destination)
print "Saved to: %s" % destination
