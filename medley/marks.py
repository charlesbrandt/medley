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

# see also:
# /c/medley/medley/sources.py

import os, sys, codecs, re
import logging
#from beats_in_space import parse_episode

from moments.timestamp import Timestamp
from moments.path import Path

def usage():
    print __doc__



class Mark(object):
    """
    
    """
    def __init__(self, tag, position, source, length=None, created=None, bytes=None, title=""):
        self.tag = tag
        #in milliseconds
        self.position = position
        self.source = source

        #only used in mortplayer
        #assuming length should be ms?
        self.length = length
        self.created = created

        #these are used in m3u lists
        self.bytes = bytes
        
        #once we've determined the real title of the mark location:
        self.title = title
        

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

    def total_seconds(self):
        return int(self.position) / 1000
    
    def as_mortplayer(self):
        """
        return a string representation needed for mortplayer bookmarks
        (location, number, name, ms1, end, utime) = line.strip().split('\t')
        """
        created = str(int(self.created.epoch() * 1000))
        return '\t'.join( [self.source, '1', self.tag, self.position, self.length, created] ) + '\n'

    def as_m3u(self, bitrate=192000):
        """
        return a string representation needed for m3u playlist bookmarks:

        (bitrate is kilobits per second)
        """
        #{name=talk2,bytes=916293,time=37},
        new_tag = self.tag.replace(',', '_')
        if self.bytes:
            result = "{name=%s,bytes=%s,time=%s}" % (new_tag, self.bytes, self.total_seconds())
        else:
            bytes_per_second = bitrate / 8.0
            bytes = int((float(self.position) * bytes_per_second) / 1000)
            result = "{name=%s,bytes=%s,time=%s}" % (new_tag, bytes, self.total_seconds())
            self.bytes = bytes
        return result


class Marks(list):
    """
    marks is a dictionary of files and their corresponding Mark objects

    can probably just use a standard dictionary for this

    (or, if you want a list of Marks for a file, a standard list should suffice)

    *2012.10.10 17:51:52
    starting with a list

    if a dictionary is needed, it can be generated with specific details
    """
    def __init__(self, source=None):
        self.source = source

    
    def from_mortplayer(self, source=None):
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

    def from_m3u(self, source=None):
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

        marks_options = []
        for line in f.readlines():
            if re.match("#EXTM3U", line):
                pass
            elif re.match("#EXTINF", line):
                line = line[8:]
                #print line
                length, title = line.split(',')
                #print "length: %s, title: %s" % (length, title)
            elif re.match("#EXTVLCOPT", line):
                #latest bookmarks:
                line = line[21:]
                parts = line.split('},')
                #reset this every time... we only want the last one
                marks_options = []
                for part in parts:
                    part = part.replace('{', '')
                    #print part
                    part = part.replace('}', '')
                    sub_parts = part.split(',')
                    if len(sub_parts) == 3:
                        fullname, fullbytes, fulltime = sub_parts
                        #print fullname, fullbytes, fulltime
                        name = fullname.split('=')[1]
                        bytes = fullbytes.split('=')[1]
                        time = fulltime.split('=')[1]

                        bytes_per_second = 24032.0
                        ms = (float(bytes) / bytes_per_second) * 1000
                        ms = int(ms)

                        ## if int(time) < 0:
                        ##     # need to figure out time based on bytes
                        ##     # sometimes vlc gives negative values 
                        ##     # that doesn't help
                        ##     # also [2012.10.12 11:24:19] 
                        ##     # not just negative values that can be wrong
                        ##     #
                        ##     # this value could change based on encoding:
                        ##     # current bytes per second:
                        ##     # 24069.11418685121107
                        ##     # 24023.08172902288413
                        ##     ms = (float(bytes) / 24032.0) * 1000
                        ##     ms = int(ms)
                        ## else:
                        ##     ms = int(time) * 1000
                        
                    else:
                        raise ValueError, "Unknown number of sub parts in bookmarks: %s" % sub_parts

                    marks_options.append( [ int(ms), name, bytes ] )
            else:
                #must have a filename here
                #now we can process mark options
                location = line
                marks_options.sort()
                for mo in marks_options:
                    ms, name, bytes = mo
                    length_ms = int(length) * 1000
                    details = Mark(name, ms, location, length_ms, bytes=bytes)
                    self.append(details)
                    
        f.close()

        return self


    def to_mortplayer(self, destination='temp.mpb'):
        """
        """
        print "saving to: %s" % destination
        #for writing unicode
        f = codecs.open(destination, 'w', encoding='utf-8')

        for mark in self:
            f.write(mark.as_mortplayer())
        f.close()


    def to_m3u(self, destination="temp.m3u", verify=False):
        f_marks = {}
        self.group_marks_by_file(f_marks)
        m3u = "#EXTM3U\r\n"
        for source in f_marks.keys():
            if (verify and os.path.exists(source)) or (not verify):
                #obj = self.get_object(i)
                #could use an ID3 library to load this information here:
                length = 0
                artist = ""
                title = os.path.basename(source)
                m3u += "#EXTINF:%s,%s - %s\r\n" % (length, artist, title)

                bmarks = []
                for mark in f_marks[source]:
                    bmarks.append(mark.as_m3u())
                bookmarks = ','.join(bmarks)
                m3u += "#EXTVLCOPT:bookmarks=%s\r\n" % bookmarks
                m3u += mark.source

                m3u += "\r\n"
            else:
                print "Ignoring. Item not found: %s" % source

        f = codecs.open(destination, 'w', encoding='utf-8')
        f.write(m3u)
        f.close()
                
        return m3u


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


class M3U(list):
    """
    have come up with many different ways to convert M3U files
    but never an object to represent one natively
    """
    def __init__(self, source=None):
        self.source = source
        self.marks = Marks()
        if source:
            self.load()

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

        marks_options = []
        for line in f.readlines():
            if re.match("#EXTM3U", line):
                pass
            elif re.match("#EXTINF", line):
                line = line[8:]
                #print line
                length, title = line.split(',')
                #print "length: %s, title: %s" % (length, title)
            elif re.match("#EXTVLCOPT", line):
                #latest bookmarks:
                line = line[21:]
                parts = line.split('},')
                #reset this every time... we only want the last one
                marks_options = []
                for part in parts:
                    part = part.replace('{', '')
                    #print part
                    part = part.replace('}', '')
                    sub_parts = part.split(',')
                    if len(sub_parts) == 3:
                        fullname, fullbytes, fulltime = sub_parts
                        #print fullname, fullbytes, fulltime
                        name = fullname.split('=')[1]
                        bytes = fullbytes.split('=')[1]
                        time = fulltime.split('=')[1]

                        bytes_per_second = 24032.0
                        ms = (float(bytes) / bytes_per_second) * 1000
                        ms = int(ms)

                        ## if int(time) < 0:
                        ##     # need to figure out time based on bytes
                        ##     # sometimes vlc gives negative values 
                        ##     # that doesn't help
                        ##     # also [2012.10.12 11:24:19] 
                        ##     # not just negative values that can be wrong
                        ##     #
                        ##     # this value could change based on encoding:
                        ##     # current bytes per second:
                        ##     # 24069.11418685121107
                        ##     # 24023.08172902288413
                        ##     ms = (float(bytes) / 24032.0) * 1000
                        ##     ms = int(ms)
                        ## else:
                        ##     ms = int(time) * 1000
                        
                    else:
                        raise ValueError, "Unknown number of sub parts in bookmarks: %s" % sub_parts

                    marks_options.append( [ int(ms), name, bytes ] )
            else:
                #must have a filename here
                #now we can process mark options
                location = line.strip()
                marks_options.sort()
                for mo in marks_options:
                    ms, name, bytes = mo
                    length_ms = int(length) * 1000
                    details = Mark(name, ms, location, length_ms, bytes=bytes)
                    self.marks.append(details)
                self.append(location)
                    
        f.close()

        return self

    def save(self, destination, verify=True, flat=False):
        """
        TODO:
        this does not yet deal with saving marks
        that can be added as needed
        see marks.to_m3u()
        """
        if destination is None:
            destination = self.source

        if destination is None:
            raise ValueError, "Need a destination sooner or later: %s" % destination
        
        print "opening: %s" % destination
        f = codecs.open(destination, 'w', encoding='utf-8')

        m3u = u"#EXTM3U\r\n"
        for item in self:
            #TODO:
            #debug path with special characters:
            #print item
            #s = Path(item)
            #if (verify and s.exists()) or (not verify):
            if (verify and os.path.exists(item)) or (not verify):
                #could use an ID3 library to load this information here:
                length = 0
                artist = u""
                title = os.path.basename(item)
                #either of these should work as long as no paths
                #have been converted to strings along the way
                #m3u += u"#EXTINF:{0}\r\n".format(title)
                m3u += u"#EXTINF:%s,%s - %s\r\n" % (unicode(length), unicode(artist), unicode(title))
                

                if flat:
                    #m3u += s.path.filename
                    m3u += title
                else:
                    m3u += item

                m3u += u"\r\n"
            else:
                print "Ignoring. Item not found: %s" % s.path

        f.write(m3u)
        f.close()
        return m3u
        


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
