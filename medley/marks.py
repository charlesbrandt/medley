#!/usr/bin/env python
"""
# By: Charles Brandt [code at contextiskey dot com]
# On: *2012.04.24 13:05:58 
# License:  MIT 

# Description:
Generalized collection of marks / position times associated with a specific media file

related to sources and player code... if you want to dig.
but a single source could have many marks associated with it (no concept of this in sources.py code)

load in the tab delimited bookmark exported by Mort Player (on Android)

"""

# see also:
# /c/medley/medley/sources.py

import os, sys, codecs, re
import logging
#from beats_in_space import parse_episode

from moments.timestamp import Timestamp
from moments.path import Path

def usage():
    print __doc__


class TextIndex():
    
    #previously Marks.save_marks
    #outputs a text list of media and track lists
    def save_marks(self, files):
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


#TODO:
#consider moving this to formats file


#previously:
#class Marks(list):
class MortplayerBookmarks(list):
    """
    focusing this class specifically on the Mortplayer Bookmark format

    A collection of marks should start showing up in many places
    and ideally should just be a list of Mark objects
    associated with a specific Content object

    format specific methods should be grouped by the format
    to avoid a collosal 'Converter' type object again.


    
    
    marks is a dictionary of files and their corresponding Mark objects

    can probably just use a standard dictionary for this

    (or, if you want a list of Marks for a file, a standard list should suffice)

    *2012.10.10 17:51:52
    starting with a list

    if a dictionary is needed, it can be generated with specific details

    """
    def __init__(self, source=None):
        self.source = source

    
    #def from_mortplayer(self, source=None):
    def load(self, source=None):
        """
        read in the source
        update the "files" dictionary with marks
        """
        if source is None:
            source = self.source

        if source is None:
            raise ValueError, "Need a source sooner or later: %s" % source
        
        print "opening: %s" % source
        #for reading unicode
        f = codecs.open(source, 'r', encoding='utf-8')

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
                #details = Mark(name, ms1, end, created, location)

                #name, position, source, length, created
                details = Mark(name, ms1, location, end, created)

                self.append(details)

        f.close()

        return self


    #def to_mortplayer(self, destination='temp.mpb'):
    def save(self, destination='temp.mpb'):
        """
        """
        print "saving to: %s" % destination
        #for writing unicode
        f = codecs.open(destination, 'w', encoding='utf-8')

        for mark in self:
            f.write(mark.as_mortplayer())
        f.close()



    def group_marks_by_file(self, files=None, source=None):
        if not source is None:
            self.from_mortplayer(source)

        if not len(self):
            raise ValueError, "no marks to process: %s" % len(self)

        if files is None:
            files = {}

        for mark in self:
            location = mark.source
            if files.has_key(location):
                files[location].append(mark)
            else:
                files[location] = [ mark ] 

        return files

    def group_marks_by_tracks(self, f_marks=None, default_pattern='bis*'):
        """
        take group_marks_by_file one step further
        and group the marks based on common tagging patterns

        does not pair sub groups with a track automatically
        this can be done elsewhere

        default_pattern can be specified based on
        what the application making bookmarks used when no tag/title supplied
        (can vary from application to application...
        e.g. filename, track title from ID3, etc)
        """
        if f_marks is None:
            f_marks = self.group_marks_by_file()

        new_f_marks = {}
        
        for key in f_marks.keys():
            #could find default pattern and insert it here instead of "start"
            file_groups = [ ]

            in_talk = False

            current_group = [ Mark("start", 0, key) ]
            for next_mark in f_marks[key]:
                if re.search('skip*', next_mark.tag) or re.search('talk*', next_mark.tag) or re.search('\+', next_mark.tag):
                    current_group.append( next_mark )
                    if re.search('talk*', next_mark.tag):
                        in_talk = True

                    #can deal with plusses externally
                    #elif re.search('\+', next_mark.tag):
                    #    plusses.append(previous_track)
                    #    plusses.append(line)

                elif in_talk:
                    #we want to skip the normal tag after an item...
                    #this usually ends the talking
                    #TODO:
                    #sometimes the end of talking
                    #and the start of the next track
                    #is the same
                    #would be nice to identify...
                    #might be one of the manual steps
                    
                    current_group.append( next_mark )
                    in_talk = False

                #this is the start of a new track / current_group
                elif re.match(default_pattern, next_mark.tag):
                    #add previous track to file_groups
                    file_groups.append(current_group)
                    current_group = [ next_mark ]

                else:
                    #probably just a description of some kind:
                    current_group.append( next_mark )
                    print "Unmatched tag: %s" % next_mark.tag

            #don't forget last group found:
            file_groups.append(current_group)
            new_f_marks[key] = file_groups
            
        return new_f_marks






    #def find_pluses(files):
    #def find_bookmarks(source):
    def find_pluses(self, source):

        log_check = re.compile('.*\.mpb$')    
        if os.path.isdir(source):
            f_marks = {}
            for root,dirs,files in os.walk(source):
                for f in files:
                    current_file = os.path.join(root, f)
                    if log_check.search(f):
                        #marks = from_mortplayer(current_file)
                        marks = Marks(current_file)
                        marks.from_mortplayer()
                        marks.group_marks_by_file(f_marks)

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

    def update_locations(self, old_prefix, new_prefix):
        """
        only update locations for loaded marks
        
        """
        for mark in self:
            #year = date[0:4]
            #prefix = '/mnt/sdcard/external_sd/podcasts/beats_in_space/'
            #new_source = os.path.join(prefix, year, date, correct_name)
            relative = Path(mark.source).to_relative(old_prefix)
            new_source = os.path.join(new_prefix, relative)
            
            if new_source != mark.source:
                logging.debug("original source: %s" % mark.source)
                logging.debug("new source: %s" % new_source)

            mark.source = new_source

    #TODO
    #haven't checked past here since converting to Marks object



    def update_locations_many_files(self, source):
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


    #TODO:
    #Move this as part of a Collection???
    def check_bookmark_availability(self, source):
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

    #TODO:
    #Move this as part of a Collection???
    def find_bookmarks(self, source):
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
