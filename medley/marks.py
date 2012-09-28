#!/usr/bin/env python
"""
# By: Charles Brandt [code at contextiskey dot com]
# On: *2012.04.24 13:05:58 
# License:  MIT 

# Description:
Generalized collection of marks / position times associated with a specific media file

related to sources and player code... if you want to dig.

although a single source could have many marks associated with it (no concept of this in sources)

load in the tab delimited bookmark exported by Mort Player (on Android)

"""

import os, sys, codecs, re
from beats_in_space import parse_episode

from moments.timestamp import Timestamp

def usage():
    print __doc__


class Marks(dict):
    """
    marks is a dictionary of files and their corresponding Mark objects

    can probably just use a standard dictionary for this

    (or, if you want a list of Marks for a file, a standard list should suffice)
    """
    pass

    

class Mark(object):
    """
    
    """
    def __init__(self, tag, position, length, created, source, title=""):
        self.tag = tag
        #in milliseconds
        self.position = position
        self.length = length
        self.created = created
        
        #once we've determined the real title of the mark location:
        self.title = title
        
        self.source = source

    def __repr__(self):
        return "%s, %s, %s, %s" % (self.position, self.tag, self.title, self.source)

    def as_time(self):
        """
        shortcut to print the position in time format
        """
        return "%02d:%02d:%02d" % self.from_milliseconds()
        
    def from_milliseconds(self, milli_seconds=None):
        """
        take a string representation of a value in milli_seconds
        convert it to hours, minutes, seconds
        """
        if milli_seconds is None:
            milli_seconds = self.position
            
        total_seconds = int(milli_seconds) / 1000
        seconds = (int(total_seconds) % 60)
        total_minutes = (int(total_seconds) / 60)
        minutes = total_minutes % 60
        hours = total_minutes / 60
        return (hours, minutes, seconds)

    def to_milliseconds(self, hours=0, minutes=0, seconds=0, ms=0):
        """
        opposite of from_milliseconds
        take hours, minutes, and seconds

        automatically set our local ms / position attribute ???
        """
        total_minutes = hours * 60 + minutes
        total_seconds = total_minutes * 60 + seconds
        return (total_seconds * 1000 + ms)

    def _get_hours(self):
        return self.from_milliseconds[0]
    hours = property(_get_hours)

    def _get_minutes(self):
        return self.from_milliseconds[1]
    minutes = property(_get_minutes)

    def _get_seconds(self):
        return self.from_milliseconds[2]
    seconds = property(_get_seconds)

    def as_mortplayer(self):
        """
        return a string representation needed for mortplayer bookmarks
        (location, number, name, ms1, end, utime) = line.strip().split('\t')
        """
        created = str(int(self.created.epoch() * 1000))
        return '\t'.join( [self.source, '1', self.tag, self.position, self.length, created] ) + '\n'

def from_mortplayer(source):
    """
    read in the source
    update the "files" dictionary with marks
    """
    print "opening: %s" % source
    #for reading unicode
    f = codecs.open(source, 'r', encoding='utf-8')

    marks = []

    for line in f.readlines():
        (location, number, name, ms1, end, utime) = line.strip().split('\t')
        if number == "1":
            created = Timestamp()
            created.from_epoch(float(utime) / 1000)
            #print "*%s %s" % (created, name)

            ## #print (location, number, name, ms1, end, utime)
            ## (hours, minutes, seconds) = convert_milliseconds(ms1)
            ## #print "%s:%02d:%02d" % (hours, minutes, seconds)

            ## ## if not end:
            ## ##     end = 0
            ## ## (hours, minutes, seconds) = convert_milliseconds(end)
            ## ## print "%s:%02d:%02d" % (hours, minutes, seconds)

            ## details = [ int(ms1), hours, minutes, seconds, name, created, location ]

            #name, position, length, created, source
            details = Mark(name, ms1, end, created, location)

            marks.append(details)

    f.close()

    return marks

def to_mortplayer(marks, destination='temp.mpb'):
    """
    """
    print "saving to: %s" % destination
    #for writing unicode
    f = codecs.open(destination, 'w', encoding='utf-8')

    for mark in marks:
        f.write(mark.as_mortplayer())

    f.close()

def group_marks_by_file(marks=None, files={}, source=None):
    if not source is None:
        marks = from_mortplayer(source)

    if marks is None:
        raise ValueError, "no marks to process: %s" % marks

    for mark in marks:
        location = mark.source
        if files.has_key(location):
            files[location].append(mark)
        else:
            files[location] = [ mark ] 

    return files

#def find_pluses(files):
#def find_bookmarks(source):
def find_pluses(source):

    log_check = re.compile('.*\.mpb$')    
    if os.path.isdir(source):
        f_marks = {}
        for root,dirs,files in os.walk(source):
            for f in files:
                current_file = os.path.join(root, f)
                if log_check.search(f):
                    marks = from_mortplayer(current_file)
                    group_marks_by_file(marks, f_marks)
                    
                    print current_file

        #pluses = find_pluses(f_marks)
        files = f_marks
        
        matched = []
        for key in files.keys():
            for mark in files[key]:
                if re.search('\+', mark.tag):
                    matched.append(mark)

        pluses = matched
        to_mortplayer(pluses)
        #print f_marks

    #print matched
    #return matched

def save_marks(files):
    for key in files.keys():
        files[key].sort()
        pre_parts = key.split('/') 
        parts = pre_parts[-1].split('.')
        destination = parts[0] + '.txt'
        f = codecs.open(destination, 'w', encoding='utf-8')

        ##TODO
        # print original bookmark source filename (in case we ever want to load them back in)

        #concise version
        for item in files[key]:
            print item
            [ ms1, hours, minutes, seconds, name, created, location ] = item
            f.write("%02d:%02d:%02d %s\n" % (hours, minutes, seconds, name))

        f.write("\n\n\n")

        #detailed (moments) version
        for item in files[key]:
            [ ms1, hours, minutes, seconds, name, created, location ] = item
            f.write("*%s\n" % created)
            f.write("%02d:%02d:%02d %s\n\n" % (hours, minutes, seconds, name))

        f.close()

def merge_bookmarks_with_tracks(source, root, plusses):
    """
    this combines one source bookmark with an html file if available
    """

    #print "getting ready to open file"
    marks = from_mortplayer(source)

    #print "grouping marks"
    f_marks = {}
    group_marks_by_file(marks, f_marks)

    # look for corresponding HTML:
    episode = None
    options = os.listdir(root)
    for o in options:
        if re.search('.*\.html$', o):
            html = os.path.join(root, o)

            # get tracklist from HTML (via episode structure)
            episode = parse_episode(html, {})
            #print episode
            #print o

    if episode:

        combined_f = os.path.join(root, "combined_list.txt")
        combined = codecs.open(combined_f, 'w', encoding='utf-8')
        #print "FMARK: %s" % f_marks
        #print f_marks.keys()
        
        for key in f_marks.keys():
            #print "%s: %s" % (key, len(f_marks[key]))

            # merge the two items as best as possible

            print ""
            print "key: %s" % key
            
            pieces = key.split('.')
            #print pieces
            part_number = pieces[-2]
            #print part_number
            part_number = part_number[-1]
            track_key = "tracks%s" % part_number
            tracks = episode[track_key]

            combos = []

            combos.append(u"source: %s\n" % key)
            plusses.append(u"source: %s\n" % key)

            title = "title%s" % part_number

            print episode[title]
            combos.append(unicode(episode[title]) + '\n')

            first_track = True
            next_mark = None
            in_talk = False
            fewer_marks = False
            previous_track = ''
            for cur_track in tracks:
                if first_track:
                    line = u"%s %s\n" % ("00:00:00", cur_track)
                    combos.append(line)
                    first_track = False
                    previous_track = line
                else:
                    track_match = False
                    while not track_match:
                        if len(f_marks[key]):
                            next_mark = f_marks[key].pop(0)
                            if re.search('skip*', next_mark.tag) or re.search('talk*', next_mark.tag) or re.search('\+', next_mark.tag):
                                line = u"%s     %s\n" % (next_mark.as_time(), next_mark.tag)
                                combos.append(line)
                                if re.search('talk*', next_mark.tag):
                                    in_talk = True
                                elif re.search('\+', next_mark.tag):
                                    plusses.append(previous_track)
                                    plusses.append(line)
                                    
                            elif in_talk:
                                #we want to skip the normal tag after an item... this usually ends
                                #the talking
                                line = u"%s     end talk (%s)\n" % (next_mark.as_time(), next_mark.tag)
                                combos.append(line)
                                in_talk = False
                            #else:
                            #this might be too specific for other podasts... using it to find unmatched tags
                            elif re.match('bis*', next_mark.tag):
                                line = u"%s %s\n" % (next_mark.as_time(), cur_track)
                                combos.append(line)
                                track_match = True
                                previous_track = line
                            else:
                                print "Unmatched tag: %s" % next_mark.tag
                                line = u"%s     %s\n" % (next_mark.as_time(), next_mark.tag)
                                combos.append(line)
                                
                        else:
                            fewer_marks = True
                            line = u"--:--:-- %s\n" % (cur_track)
                            combos.append(line)
                            track_match = True
                


            #report any length discrepencies
            if fewer_marks:
                print "Not enough marks to match to all tracks"
                combos.append(u"Not enough marks to match to all tracks\n")
            elif len(f_marks[key]):
                #print the remaining items
                for next_mark in (f_marks[key]):
                    line = u"%s     %s\n" % (next_mark.as_time(), next_mark.tag)
                    combos.append(line)
                print "More marks than tracks: %s" % len(f_marks[key])
                combos.append(u"More marks than tracks: %s\n" % len(f_marks[key]))
            else:
                print "PERFECT MATCH"
                combos.append(u"PERFECT MATCH\n")

            combos.append('\n')
            for c in combos:
                combined.write(c)
            #this gives ascii errors (!) python 2.7
            #combined.writelines(combos)

            #for c in combos:
            #    print c

        combined.close()

    else:
        print "No episode HTML available for: %s" % root

    print ""


def merge_all_bookmarks_with_tracks(source):
    plusses = []
    log_check = re.compile('.*\.mpb$')    
    if os.path.isdir(source):
        for root,dirs,files in os.walk(source):
            for f in files:
                current_file = os.path.join(root, f)
                if log_check.search(f):
                    #print current_file
                    #plusses.append(root + "\n")
                    merge_bookmarks_with_tracks(current_file, root, plusses)
                    plusses.append("\n")

        plus_f = os.path.join(source, 'plusses.txt')
        plus_file = codecs.open(plus_f, 'w', encoding='utf-8')
        for p in plusses:
            plus_file.write(p)
        plus_file.close()

def update_locations(source):
    """
    go through all bookmark files (mpb) and update any old locations to be the new one in use
    (don't want to lose those marks!)
    """
    log_check = re.compile('.*\.mpb$')    
    if os.path.isdir(source):
        for root,dirs,files in os.walk(source):
            for f in files:
                current_file = os.path.join(root, f)
                if log_check.search(f):

                    marks = from_mortplayer(current_file)
                    print current_file
                    for mark in marks:
                        #print mark.source
                        parts = mark.source.split('/')
                        name_parts = parts[-1].split('-')

                        #print len(name_parts)
                        if len(name_parts) == 3:
                            #print "new name format: %s" % parts[-1]
                            correct_name = parts[-1]
                            date = correct_name.split('-')[1]                        
                        else:
                            #print "old name format: %s" % parts[-1]
                            date = ''.join(name_parts[1:4])
                            correct_name = '-'.join( [ name_parts[0], date, name_parts[-1] ] )
                            #print correct_name

                        year = date[0:4]
                        prefix = '/mnt/sdcard/external_sd/podcasts/beats_in_space/'
                        new_source = os.path.join(prefix, year, date, correct_name)
                        if new_source != mark.source:
                            print mark.source
                            print new_source
                            
                        mark.source = new_source

                    #save the update
                    to_mortplayer(marks, current_file)


def check_bookmark_availability(source):
    """
    find bookmarks and directories with text files available

    (should also populate f_marks via group_marks_by_file)
    """
    log_check = re.compile('.*\.mpb$')    
    text_check = re.compile('.*\.txt$')    
    f_marks = {}
    if os.path.isdir(source):
        for root,dirs,files in os.walk(source):
            bookmark_found = False
            for f in files:
                current_file = os.path.join(root, f)
                if log_check.search(f):
                    #print current_file

                    marks = from_mortplayer(current_file)
                    group_marks_by_file(marks, f_marks)
                    bookmark_found = True
            if not bookmark_found:
                print "No bookmarks for: %s" % root
                for f in files:
                    if text_check.search(f):
                        print f
                print ""

    return f_marks


def find_bookmarks(source):
    """
    find and load all bookmarks under source
    return results
    """
    log_check = re.compile('.*\.mpb$')    
    f_marks = {}
    if os.path.isdir(source):
        for root,dirs,files in os.walk(source):
            bookmark_found = False
            for f in files:
                current_file = os.path.join(root, f)
                if log_check.search(f):
                    #print current_file
                    marks = from_mortplayer(current_file)
                    group_marks_by_file(marks, f_marks)
                    
    return f_marks


def main():
    #requires that at least one argument is passed in to the script itself
    #(through sys.argv)
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

        #from_mortplayer_original(source)

        #update_locations(source)
        #find_bookmarks(source)
        #check_bookmark_availability(source)
        #find_pluses(source)
        merge_all_bookmarks_with_tracks(source)
        
    else:
        usage()
        exit()
        
if __name__ == '__main__':
    main()
