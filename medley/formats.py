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

import os, sys, codecs, re
import logging

from moments.timestamp import Timestamp
from moments.path import Path

from content import Mark, Content

def usage():
    print __doc__

class M3U(list):
    """
    have come up with many different ways to convert M3U files
    but never an object to represent one natively

    the most simple format is simply a list of strings,
    where each string represents a path to a specific media

    """
    def __init__(self, source=None):
        self.source = source

        if source:
            self.load()

    def load(self, source=None, look_for_meta=False):
        """
        read in the source
        update the 'self.marks' dictionary with found marks

        if look_for_meta,
        scan for json file in same directory as media file
        then load Content data
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
                #length, title = line.split(',')
                parts = line.split(',')
                length = parts[0]
                title = parts[1]
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
                content = Content()
                content.media.append(location)

                #TODO:
                #update Content filename and root with location data

                #could also look for json data and load it if available.
                
                marks_options.sort()
                for mo in marks_options:
                    #TODO:
                    #could check for duplicate marks here
                    ms, name, bytes = mo
                    length_ms = int(length) * 1000
                    details = Mark(name, ms, location, length_ms, bytes=bytes)
                    content.marks.append(details)
                self.append(content)

                if look_for_meta:
                    content.load()
                    
        f.close()

        return self


    def save(self, destination, verify=False, flat=False):
        """
        Save the M3U to a file
        """
        if destination is None:
            destination = self.source

        if destination is None:
            raise ValueError, "Need a destination sooner or later: %s" % destination
        
        print "opening: %s" % destination
        f = codecs.open(destination, 'w', encoding='utf-8')

        m3u = u"#EXTM3U\r\n"
        for item in self:
            #check if item is a string or a Content object
            if isinstance(item, Content):
                path = item.media[0]
                bmarks = []
                for mark in item.marks:
                    bmarks.append(mark.as_m3u())
                bookmarks = ','.join(bmarks)
            else:
                path = item
                bookmarks = ''
                
            if (verify and os.path.exists(path)) or (not verify):
                #TODO:
                #could use an ID3 library to load this information here:
                length = 0
                artist = u""
                title = os.path.basename(path)

                #either of these should work as long as no paths
                #have been converted to strings along the way
                #m3u += u"#EXTINF:{0}\r\n".format(title)
                m3u += u"#EXTINF:%s,%s - %s\r\n" % (unicode(length), unicode(artist), unicode(title))
                
                if bookmarks:
                    m3u += "#EXTVLCOPT:bookmarks=%s\r\n" % bookmarks


                if flat:
                    #m3u += s.path.filename
                    m3u += title
                else:
                    m3u += path

                m3u += u"\r\n"
            else:
                print "Ignoring. Item not found: %s" % path

        f.write(m3u)
        f.close()
        return m3u
        



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


    def to_m3u(self, destination="temp.m3u", verify=False):
        """
        this is a helper for going directly from mortplayer to m3u

        it is also possible to convert to a standard M3U object first
        then save from there.
        """
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


class Converter(object):
    """
    Sources generator
    
    a collection of routines used to convert to and from a Sources list

    approaches Sources generation from many different levels

    rather than bog down and clutter the Sources object directly
    can just generate or convert it here
    """
    
    def __init__(self, path=None, sources=None):
        """
        accept a path as the source
        generate the corresponding Sources object

        probably a good idea to pass sources in, so that when Converter
        is destroyed, sources doesn't go with it

        if that's the case, makes sense,
        but seems that returning souce should keep it around in caller
        """
        self.path = path

        #if path is not None:
            
        ## if sources is None:
        ##     self.sources = Sources()
        ## else:
        ##     self.sources = sources

    def from_file(self, path=None, sort=False):
        """
        the default way to try to load a file
        can add some intelligence based on file extensions here
        """
        if path is None:
            if self.path is None:
                raise ValueError, "Need a filename to load from file"
            else:
                path = self.path

        sources = self.from_journal(path, sort)
        return sources
            

    def from_entry(self, entry):
        """
        take one journal entry
        and look for Sources items within it
        """
        sources = Sources()

        #print "ENTRY: %s" % entry.render()
        for line in entry.data.splitlines():
            source = Source()
            #print "Pre Source: %s, entry: %s" % (source, source.entry.render())
            if re.search("\ -sl\ ", line):
                #this requires the first 3 items to be:
                # # -sl [nums] [file]
                # otherwise parts will be off
                # see replace.txt
                parts = line.split(' ', 3)
                try:
                    sl_pos = parts.index('-sl')
                except:
                    print "SL found, but incorrect format:"
                    print e.render()
                    exit()
                jumpstr = parts[sl_pos+1]
                jumps = Jumps(jumpstr)
                
                try:
                    source_file = parts[sl_pos+2]
                except:
                    print "no source file in parts: %s" % parts
                    print line
                    print

                #get rid of surrounding quotes here
                source_file = source_file.replace('"', '')
                
                source.path = source_file
                source.jumps = jumps
                source.entry = entry
                #print "adding source: %s" % source
                sources.append( source )
                
            elif line.strip():
                #this will not work with entries that have file paths
                #and other comments/text in them:

                #'# -sl ' should be caught by previous case
                #could verify that line starts with either a '/' 'http:'
                source_file = line.strip()
                if re.match('^media', source_file):
                    source_file = source_file.replace('media/', '')
                    source_file = '/c/' + source_file
                #elif re.match('^graphics', source_file):
                
                ## if re.match('^/', source_file):
                ##     source = Source()
                ##     source.path = source_file
                ##     source.entry = entry
                ##     #print "adding source: %s" % source
                ##     self.sources.append( source )
                ## else:
                ##     print "Non Source: %s" % source_file

                source.path = Path(source_file)
                source.entry = entry
                #print "entry: %s" % entry.render()
                #print "adding source: %s" % source
                sources.append( source )

            #if source.entry:
            #    print "Source: %s, entry: %s" % (source, source.entry.render())

                
        return sources

    def from_entries(self, entries, sources=None):
        """
        take a list of moments/entries
        for each line in the entry
        see if it will work as a playlist item
        add if so
        """
        if not sources:
            sources = Sources()
        for e in entries:
            sources.extend(self.from_entry(e))
            
        sources.update()
        return sources

    #def condense_and_sort(self, destination=None):
    def condense_and_sort(self, sources=None):
        """
        whatever is in the list,
        count the number of times items show up in the list
        (return the frequency of those items)
        and sort items by that frequency
        and return a condesed list in that order
        """
        #if destination is None:
        destination = Sources()
        
        ## freq = Association()
        ## for i in pl:
        ##     freq.associate(i, i[0])
        ## item_lists = freq.items_by_frequency()
        ## new_list = []
        ## #now have a list of:
        ## #[ [file_path, list_of_original_playlist_items], ..]
        ## for i in item_lists:
        ##     longest = ['', []]
        ##     for playlist_item in i[1]:
        ##         if len(playlist_item[1]) >= len(longest[1]):
        ##             longest = playlist_item
        ##     #print len(longest[1])
        ##     new_list.append(longest)

        tally = {}

        print "Starting size: %s" % len(sources)

        #at this point we will be losing any entry associated
        #in order to condense
        #this will also lose any tag data
        #we can look up one of these entries later
        #no guarantee which one will be reassociated
        # could go through all entries later and tally up tags there
        # don't want to do that just yet though
        for i in sources:
            #print i
            #print type(i)
            i.jumps.sort()
            key = i.as_key()

            if tally.has_key(key):
                tally[key] += 1
            else:
                tally[key] = 1

        #get the keys and values
        items = tally.items()

        #convert top items to lists instead of default tuple returned by dict
        new_items = []
        for i in items:
            new_items.append( list(i) )
        items = new_items

        #NOTE ON WHAT IS STORED IN THE KEY:
        ## if self.jumps:
        ##     key = ( self.path, tuple(self.jumps) )
        ## else:
        ##     key = ( self.path )
        ## return key
        #
        #AND ITEMS CONTAIN LISTS OF (KEY, VALUE)
        #where value is the number of times a key appeared

        #condense items:
        condensed = items[:]
        for i in items:
            # see if we have jumps to consider
            if len(i[0]) > 1:
                #could be more than one condensed(c) that has jumps as subset...
                #should stop after we find one that matches
                #(hence using 'while' instead of 'for')
                #if we find a subset, add the count of the subset
                #to the count of the superset
                #and then remove the subset from the condensed list
                pos = 0
                match = False
                while not match:
                    c = condensed[pos]
                    #if condensed.key.path == item.key.path
                    #and we have jumps to consider:
                    if (c[0][0] == i[0][0]) and (len(c[0]) > 1):
                        #both have times
                        #check if either is a subset of the other
                        cset = set(c[0][1])
                        iset = set(i[0][1])
                        if len(cset.difference(iset)) == 0:
                            #same set!
                            #could be the same item
                            pass
                        elif cset.issubset(iset):
                            #update tally i in condensed
                            pos = condensed.index(i)
                            condensed[pos][1] += c[1]
                            print "found subset: %s of: %s. current length: %s" % ( cset, iset, len(condensed))
                            condensed.remove(c)
                            print "new length: %s" % len(condensed)
                            match = True
                        elif iset.issubset(cset):
                            #update tally i in condensed
                            pos = condensed.index(c)
                            condensed[pos][1] += i[1]
                            print "found subset: %s of: %s. current length: %s" % ( iset, cset, len(condensed))
                            condensed.remove(i)
                            print "new length: %s" % len(condensed)
                            match = True
                        else:
                            #print "times didn't match"
                            pass
                    pos += 1
                    if pos >= len(condensed):
                        #maybe no match, exit while loop
                        match = True

            #must not have any jumps in this playlist item
            else:
                #in this case, the list should have been the same
                pass
            
        items = condensed
        print "After Condensing: %s" % len(items)

        # see Items.sort()

        #need to sort based on second item in the list, not the first...
        #not sure how to do this with sort...
        #I think there is a better way than this:
        #swap positions:
        new_items = []
        for i in items:
            new_items.append( (i[1], i[0]) )
        new_items.sort()
        new_items.reverse()
        items = []
        for i in new_items:
            items.append( i[1] )

        print "After Sorting: %s" % len(items)

        #re-assign the original entry with an item if we can
        #
        #this will not catch the case when jumps were merged into a larger set
        #will lose entry association in that case
        for i in sources:
            key = i.as_key()
            if key in items:
                pos = items.index(key)
                items[pos] = [ i.path, i.jumps, i.entry ]

        print "After Adding original entry back: %s" % len(items)


        #regenerate a new Sources object:
        for i in items:
            source = Source()
            source.path = i[0]
            if len(i) > 1:
                source.jumps = i[1]
            if len(i) > 2:
                source.entry = i[2]
            destination.append(source)

        #should be smaller or the same if condensing and sorting is working:
        print "Ending size: %s" % len(destination)

        destination.update()
        return destination
    
    def from_copy_all_urls(self, data):
        """
        parse a buffer that contains output from copy all urls as a list

        for now skipping title lines... will need those for export
        """
        
        for line in data.splitlines():
            if line.startswith('http://') or line.startswith('/'):
                self.append(line.strip())

    def from_journal(self, path, sources=None, sort=False):
        """
        use from_entries, and condense_and_sort()
        """
        j = load_journal(path)
        print len(j)
        print j
        for i in j:
            print i.render()

        sources = self.from_entries(j, sources)
            
        print len(sources)
        if sort:
            #condense and sort will change the order of an entry list
            new_sources = self.condense_and_sort(sources)
            return new_sources
        else:
            return sources

    def save(self):
        pass

    def to_journal(self, destination, sources, tags=[], skip_dupes=False):
        """
        use from_entries, and condense_and_sort()
        """
        j = load_journal(destination)
        print len(j)
        print j

        if skip_dupes:
            j.associate_data()
            for source in sources:
                if not j.datas.has_key(str(source.path)+'\n\n'):
                    moment = source.as_moment()
                    moment.tags.union(tags)
                    j.update_entry(moment)
        else:
            for source in sources:
                moment = source.as_moment()
                moment.tags.union(tags)
                j.update_entry(moment)
                
        j.to_file(destination)

    def to_links(self, prefix='/dir'):
        links = ''
        for i in self:
            obj = self.get_object(i)
            links += url_for(obj.custom_relative_path(prefix=prefix), qualified=True)
            links += "\r\n"
        return links

    def to_xspf(self, filename=None):        
        xspf = StringIO.StringIO("Hello")
        xml = XmlWriter(xspf, indentAmount='  ')

        xml.prolog()
        xml.start('playlist', { 'xmlns': 'http://xspf.org/ns/0/', 'version': '1' })
        xml.start('trackList')

        for line in self:
            #line = line.rstrip('\n')

            url = None
            if line.startswith('http://'):
                url = line
            else:
                obj = self.get_object(line)
                if obj:
                    url = url_for(obj.custom_relative_path(prefix="/sound"), qualified=True)
                    #url = url_for(url_escape(obj.custom_relative_path(prefix="/sound")), qualified=True)
                #url = 'file://' + urllib.pathname2url(line)

            if url:
                xml.start('track')
                xml.elem('location', url)
                xml.elem('title', os.path.basename(line))
                #if options.add_annotation:
                #        xml.elem('annotation', createAnnotation(url))

                xml.end() # track

        xml.end() # trackList
        xml.end() # playlist
        
        xspf.seek(0)
        return xspf.read()



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

