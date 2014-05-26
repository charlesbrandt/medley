"""
Content related objects.

What best describes this object? Going with Content... other options were:
Thing, Item, Medium, Source, 

These are too specific:
Song, Podcast, Album, Image, Book, Movie, Scene, 

"""
import os, re, copy
import hashlib

from helpers import save_json, find_json, load_json, get_media_dimensions, get_media_properties

from moments.path import Path
from moments.timestamp import Timestamp
from moments.tag import to_tag
#for history:
from moments.journal import Journal
from moments.log import Log

class Mark(object):
    """
    position time associated with a specific media file

    AKA:
    jump, bookmark, markpoint/MarkPoint
    """
    def __init__(self, tag='', position=0, source=None, length=None, created=None, bytes=None, title="", seconds=None):
        #*2013.06.16 08:24:49 
        #not sure how tag and title differ... (see note below)
        #also what about 'name' or 'description' (better in a segment)

        #tag is a user specified tag or category ('work', 'chill', 'other')
        #if included as part of a segment, should update the segment.tags too
        self.tag = tag
        
        #once we've determined the real title of the mark location:
        #self.title = title
        #this is better represented in a segment instead of a mark

        #in milliseconds
        self.position = int(position)
        self.source = source

        if seconds:
            self.position = float(seconds) * 1000
        
        #only used in mortplayer
        #assuming length should be ms?
        self.length = length
        if created is None:
            self.created = Timestamp()
        else:
            self.created = created

        #these are used in m3u lists
        self.bytes = bytes
        

    def __repr__(self):
        #return "%s, %s, %s, %s\n" % (self.position, self.tag, self.title, self.source)
        return "%s, %s, %s\n" % (self.position, self.tag, self.source)

    def as_time(self):
        """
        shortcut to print the position in time format
        """
        return "%02d:%02d:%02d" % self.as_hms()

    def from_time(self, text):
        parts = text.split(':')
        if len(parts) == 3:
            self.from_hms(int(parts[0]), int(parts[1]), int(parts[2]))
        elif len(parts) == 2:
            self.from_hms(minutes=int(parts[0]), seconds=int(parts[1]))
        else:
            raise ValueError, "Unknown number of parts for time: %s (%s)" % (parts, len(parts))
            
        
    #def from_milliseconds(self, milli_seconds=None):
    def as_hms(self, milli_seconds=None):
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

    def from_hms(self, hours=0, minutes=0, seconds=0, ms=0):
        """
        opposite of as_hms
        take hours, minutes, and seconds

        automatically set our local ms / position attribute ???
        """
        total_minutes = hours * 60 + minutes
        total_seconds = total_minutes * 60 + seconds
        self.position = (total_seconds * 1000 + ms)
        return self.position

    def _get_hours(self):
        return self.as_hms[0]
    hours = property(_get_hours)

    def _get_minutes(self):
        return self.as_hms[1]
    minutes = property(_get_minutes)

    def _get_seconds(self):
        return self.as_hms[2]
    def _set_seconds(self, seconds):
        self.position = seconds * 1000
    seconds = property(_get_seconds, _set_seconds)

    def total_seconds(self):
        #return int(self.position) / 100
        return float(self.position) / 1000

    def as_tuple(self):
        """
        the two main attributes of a Mark are:
        the position
        and
        the tag
        return these as a tuple for easy jsonification

        when storing these with a content item, we already know self.source
        """
        new_tag = self.tag.replace(',', '_')
        return (self.total_seconds(), new_tag)

    # FORMAT SPECIFC CONVERTERS:
    
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



#I don't think a PositionList is necessary here...
#that should be utilized at the playlist/segment level
#class MarkList(PositionList):
#class Jumps(PositionList):

# aka Marks, Jumps, or MarkPoints
class MarkList(list):
    """
    instead of a list of integers (as in MarkListSimple)
    use acutal Mark objects
    this adds complexity, but also makes the object more powerful
    
    includes methods for comparing one list to anther for easier merging

    this is not format specific
    for a related object, see: formats.MortplayerBookmarks
    """
    def __init__(self, items=[], comma=''):
        super(MarkList, self).__init__()
        
        #self.extend(items)
        for item in items:
            if isinstance(item, Mark):
                self.append(item)
            else:
                #incase we get a list of lists:
                mark = Mark(*item)
                self.append(mark)

        if comma:
            self.from_comma(comma)

    #over-ride default sort...
    #sort based on eacy mark position
    def sort(self):
        """
        sorted() function is also available
        """
        super(MarkList, self).sort(key=lambda mark: mark.position)
            
    def to_tuples(self):

        result = []
        for mark in self:
            result.append(mark.as_tuple())
        return result

    def from_tuples(self, tuples):
        for t in tuples:
            #print "TUPLE: %s" % t
            mark = Mark()
            mark.seconds = t[0]
            mark.tag = t[1]
            self.append(mark)
            
    def segment_helper(self, segment, new_segments, parent, titles, title_index):
        """
        need to do this step at the end of every segment
        two separate places where this occurrs in make_segments, so abstracting
        """
        #now that we have a full segment, apply the right title to it:
        #(if titles are available)
        cur_title = ''
        if len(titles) and (len(titles) > title_index):
            cur_title = titles[title_index]
            title_index += 1
        elif len(titles) and (len(titles) <= title_index):
            print "Not enough titles to apply to segments"
            #print "extra segments: %s tracks, %s segments" % (len(titles), segment_count)

        if len(new_segments):
            #process all segments and add a suffix to title
            new_segments.append(segment)
            count = 1
            for segment in new_segments:
                if not segment.title:
                    if segment.end:
                        #print "Segment End: ->%s<-, Segment Start: ->%s<-" % (segment.end.position, segment.start.position)
                        segment_len = (segment.end.position - segment.start.position) / 1000
                        segment_len = int(segment_len)
                    else:
                        segment_len = '?'
                    new_title = "%s - Part %s - %s seconds" % (cur_title, count, segment_len)
                    segment.title = new_title
                    count += 1
                    
                parent.add_segment(segment)
        else:
            segment.title = cur_title
            #add previous track to parent
            parent.add_segment(segment)

        return title_index

    def make_segments(self, parent, default_pattern="", titles=[], reset_id=True):
        """
        assumes all marks are from the same file
        (typical, but not required)

        rather than make groups of marks,
        just make segments, as intended

        parent is the main Content object that will hold all of these segments

        if titles are passed in here,
        can use the distinction between sub_segment and segment
        to only apply titles to segments
        (can try to do this outside of method, but might be harder)
        """
        if not titles:
            #get titles from parent content object:
            titles = parent.titles
        
        groups = [ ]

        #reset segment ID
        #doesn't make sense to keep track when re-merging everything
        if reset_id:
            parent.next_segment_id = 1

        if not default_pattern:
            #might still be none here, but that's ok...
            #maybe just blank is enough
            default_pattern = parent.track_prefix
        else:
            #want to keep track of the latest one passed in, if it is.
            parent.track_prefix = default_pattern
            
        in_talk = False

        last_mark = None

        #clear this out for subsequent calls
        parent.segments = []

        title_index = 0
        segment_count = 0

        #handle special cases when first segment is sub_segment:
        #not sure that this is what we want...
        #first tag may be talk, but it may be late in the first song
        #first_segment = True
        
        segment = Content()
        segment.status = ''
        start = Mark("start", 0)
        segment.start = start
        segment.marks.append(start)

        #used for things like talk and caller segments
        sub_segment = Content()
        sub_segment.status = ''

        #buffer for holding segments that are not finished
        #due to talk subsegments
        new_segments = []
        
        #current_group = [ Mark("start", 0, key) ]
        #for next_mark in f_marks[key]:
        for next_mark in self:
            #print
            #print default_pattern
            #print next_mark.tag
            if re.search('skip', next_mark.tag) or re.search('Skip', next_mark.tag) or re.search('\+', next_mark.tag):
                segment.marks.append( next_mark )
                tags = next_mark.tag.split(' ')
                if '-' in tags:
                    tags.remove('-')
                segment.tags.extend(tags)

            elif re.search('talk', next_mark.tag) or re.search('Talk', next_mark.tag) or re.search('call', next_mark.tag) or re.search('Call', next_mark.tag):
                    in_talk = True

                    #split the current track up into segments too
                    segment.end = next_mark
                    #add previous track to parent
                    new_segments.append(segment)

                    ## if first_segment:
                    ##     sub_segment.start = start
                    ##     sub_segment.marks.append(start)

                    ## else:
                    ##     sub_segment.start = next_mark

                    sub_segment.start = next_mark
                    sub_segment.marks.append( next_mark )
                    sub_segment.title = next_mark.tag

            elif in_talk:
                #we want to skip the normal tag after an item...
                #this usually ends the talking
                #
                #sometimes the end of talking
                #and the start of the next track
                #is the same
                #would be nice to identify...
                #might be one of the manual steps
                #
                #this is up to the user to create 2 marks,
                #one right after the other to signal these subsequent ends

                #segment.marks.append( next_mark )

                sub_segment.end = next_mark
                sub_segment.marks.append( next_mark )

                new_segments.append(sub_segment)
                #parent.add_segment(sub_segment)
                    
                ## if first_segment:
                ##     #get rid of initial (default) (first) segment start:
                ##     segment.marks.pop()
                        
                ##     segment.start = next_mark
                ##     segment.marks.append(next_mark)
                ##     first_segment = False

                #reset sub_segment
                sub_segment = Content()
                sub_segment.status = ''

                segment = Content()
                segment.status = ''
                segment.start = next_mark
                segment.marks.append(next_mark)
                
                in_talk = False

            #this is the start of a new track / segment
            #aka self.track_prefix
            #
            #sometimes blank tags may indicate a new mark:
            elif ((default_pattern and re.match(default_pattern, next_mark.tag))
                  or not next_mark.tag):
                segment.end = next_mark
                segment_count += 1

                title_index = self.segment_helper(segment, new_segments, parent,
                                                  titles, title_index)
                #clear these out
                new_segments = []
                
                segment = Content()
                segment.status = ''
                segment.start = next_mark
                segment.marks.append(next_mark)

            else:
                #probably just a description of some kind:
                segment.marks.append(next_mark)
                segment.tags.extend(next_mark.tag.split(' '))
                print "Unmatched tag: %s" % next_mark.tag

            #save the previous item for the next time around
            #last_mark = next_mark

        if len(titles) > segment_count:
            print "Extra titles available: %s titles, %s segments" % (len(titles), segment_count)

        #last segment doesn't need an end mark...
        #that should signal play to end
        
        #don't forget last group found:
        #parent.add_segment(segment)
        self.segment_helper(segment, new_segments, parent, titles, title_index)


        ## #new_f_marks[key] = groups
        ## return groups

    def make_segments_simple(self, parent, titles=[], reset_id=True):
        """
        a simpler version of make_segments

        this version assumes all marks indicate a new segment
        instead of searching for only matching expressions
        
        parent is still the main Content object that will hold all of these segments
        """
        groups = [ ]
        #reset segment ID
        #doesn't make sense to keep track when re-merging everything
        if reset_id:
            parent.next_segment_id = 1

        last_mark = None

        #clear this out for subsequent calls
        parent.segments = []

        title_index = 0
        segment_count = 0

        segment = Content()
        segment.status = ''
        start = Mark("start", 0)
        segment.start = start
        segment.marks.append(start)

        for next_mark in self:
            print
            print next_mark.tag
            segment.end = next_mark
            segment_count += 1

            #title_index = self.segment_helper(segment, new_segments, parent,
            #                                  titles, title_index)
            
            #add previous track to parent
            parent.add_segment(segment)

            segment = Content()
            segment.status = ''
            segment.start = next_mark
            segment.marks.append(next_mark)
            segment.title = next_mark.tag

        #get last one:
        parent.add_segment(segment)


    def add_track_numbers(self):
        """
        add numbers to each mark.tag
        according to position
        """
        self.sort()

        count = 1
        for mark in self:
            if not re.match('\d', mark.tag):
                mark.tag = "%s. %s" % (count, mark.tag)
            count += 1
        
    def extract_titles(self):
        """
        go through the list of marks we have
        and generate a list of titles

        this can be useful for tagging
        """
        self.sort()
        titles = []
        for mark in self:
            titles.append(mark.tag)
        return titles

    def from_comma(self, source):
        """
        split a comma separated string into jumps
        """
        temps = source.split(',')
        for j in temps:
            try:
                mark = Mark()
                mark.seconds = int(j)
                self.append(mark)
            except:
                print "could not convert %s to int from: %s" % (j, source)
        return self
    
    def to_comma(self):
        """
        combine self into a comma separated string
        """
        temp = []
        for j in self:
            seconds = j.total_seconds()
            if seconds not in temp:
                temp.append(str(seconds))
        jump_string = ','.join(temp)
        return jump_string

    def relate(self, compare):
        """
        take another list of items
        see if we are a subset, superset, or how many items in common there are
        returns a tuple:
        (int(items_in_common), description_of_relationship)
        where description is one of 3:
        subset
        superset
        same
        different

        requires that all items in both lists are useable in a python set
        i.e. distinct hashable objects
        (source objects themselves won't work)

        may want this to be part of general Items object
        """
        response = ''
        local = set(self)
        other = set(compare)
 
        #check if either is a subset of the other
        #cset = set(c[0][1])
        #iset = set(i[0][1])
        
        common = local.intersection(other)
        
        if len(local.difference(other)) == 0:
            #same set!
            #could be the same item
            response = 'same'
        elif local.issubset(other):
            response = 'subset'
        elif other.issubset(local):
            response = 'superset'
        else:
            response = 'different'

        return (len(common), response)


class Content(object):
    """
    Object to hold details of a particular piece of content (media)

    content varies wildly in scope
    
    could be:
        
        - a simple audio file (.wav, .mp3) representing a song
        - a podcast or mix tape containing many songs or segments
        - a movie clip
        - maybe something as simple as an image

    the main content often has supporting meta data
    (e.g. cover art, etc)
    
    or multiple, varying instances of the same content
    (e.g. different bitrates, non-compressed, different resoultions)

    this is a place to draw those together and track meta data
    """
    def __init__(self, source=None, content={}, root=None, base_dir='', debug=False):
        """
        few different ways to initialize an item of content:

          - can pass a specific media file as source,
            then look for meta data in a local json file

          - can pass a raw dictionary representation of the content meta data
            (often loaded from a json file)

          - root top-most content item for nesting content objects (not a path)
            (if it's not passed in here, child segments are not set correctly)

        NOTE:
        if content is passed in, it will be modified,
        which will modify source object
        """
        #root is no longer used for this purpose:
        #"the root location relative to collection base"
        #now it is a reference to the top most Content object in which
        #this Content object is contained.
        #self.root = root

        #everything leading up to the base_dir 
        #this is the start of the collection (collection root path)
        self.drive_dir = ''

        #aka path from collection root
        #relative path for other content
        #might want to pass this in if creating a new Content object
        #so that drive_dir will get initialized correctly too
        self.base_dir = base_dir

        #keep track of where this object's meta data is stored:
        self._json_source = ''
        
        #the default content/media related filename associated with the content
        #moving this to a property (like path), to assist with searching
        self._filename = ''

        #the md5 checksum hash for the main file
        self.hash = ''
        #this might help locate previously generated meta data
        #without knowing anything else about the file
        #similar to MuzicBrainz?

        # store a list of local media files,
        # along with dimensions if we calculate those
        # (could be other properties of the media to store)
        #
        # if there is more than one media file, media[0] is the default
        #
        # if there are multiple media files that comprise a single Content
        # object, those might be better represented in self.segments
        self.media = []


        #our title
        #not to be confused with titles, which are used with segments and marks
        self.title = ''
        self.description = ''
        #when content was created or published (according to publisher)
        self.timestamp = None

        self.added = ''
        self.visited = ''

        self.sites = []

        self.people = []
        self.tags = []

        #seeing more applications for this
        #aka thumbnail
        #aka default_image
        #might be slightly redundant if the content in reference *is* an image
        #but even then, there could be a default, smaller version
        #plus, totally optional
        self.image = ''
        
        self.marks = MarkList()
        #it is common to keep a separate list of titles
        #that are then paired with marks to create segments
        #this is the way many marks+titles are imported from other sources
        #these are usually stored as remainder['tracks']
        self.titles = []
        self.segments = []

        #using a segment id (immutable)
        #to help identify and reconnect an isolated segment
        #with the correct main Content source file
        #for subsequent updates
        #
        #e.g. a single sub-track segment in a podcast
        #could be on another playlist
        #and editing meta data on that segment in that playlist 
        #will open + save changes to the original main Context json source file
        #
        #this is facilitated by a self.add_segment method
        #
        #ok for root Content object to have blank segment_id
        #only needed if segments exist
        #
        #segments should list the full path of segment_ids from root to self
        #e.g. 1_4_2_1 (5 layers deep)
        self.segment_id = ''
                
        #starting at 1 here... not an index, just an id
        self.next_segment_id = 1

        #the regular expression used to determine a new track
        #when calling make_segments
        #(empty strings are also matched by default)
        self._track_prefix = ''
        


        #this will allow Content objects to be recursively used in segments
        #consider: anything useful from a tree structure?
        #maybe too much with trees... pretty simple here.
        #
        # should we store in seconds (float)?
        # seconds should be flexible enough for most formats
        # or should it be a mark?
        # probably should be a Mark, converted to total_seconds
        self.start = Mark()
        self.end = None

        # there are many different states that a piece of content could be in
        # depending on the process being used to parse 
        #instead of complete, using a more general status field
        #can be customized based on process used to add/update meta data
        self.status = 'new'

        self.remainder = {}

        #keep a log of when actions happened:
        #used to do this with Moment logs to track media plays
        #not processing log (e.g. loading into a Journal)
        #self.history = ""
        #to make this easier, use a Journal to help with formatting:
        self.history = Journal()
        self.history.make("Created", ["created"])

        #these attributes are generated and assigned later
        #no need to store them with a json file / dict

        #these should be used for segements and sub-segments
        #in order to load and save changes to segments
        #that are located out of context from original Content root
        self.parent = None
        if root is None:
            self.root = self
        else:
            self.root = root



        #deal with what was passed in now:
        #i.e. autoload!

        if content and source:
            raise ValueError, "Cannot initialize Content object with both source and dictionary: %s, %s" % (source, content) 

        elif content:
            #what was passed in for manual initialization:
            #store this for subsequent call to load:
            self.content = content
            self.load()

        elif source:
            
            #we might not have self.json_source yet,
            #but we know we have source
            #source_dir = os.path.dirname(self.json_source)
            source_dir = os.path.dirname(source)


            # json file to save and load from
            #this is the best way to initialize previous Content object:
            #ok to include full path here...
            self.json_source = find_json(source)
            #print "FOUND SOURCE: %s" % self.json_source
            #make sure something was found:
            if self.json_source:
                self.load(self.json_source)
            else:
                #json_source does not exist yet
                #set up some default destinations for json_source
                spath = Path(source)
                json_name = spath.name + ".json"
                self.json_source = os.path.join(source_dir, json_name)

            #check if what is stored in file is out of date
            #based on json_source location ...

            if self.json_source != source:
                #must have been passed something besides a json path
                #do some checks to see if there is anything we can use:
                # - updated filename
                new_name = os.path.basename(source)
                if new_name and new_name != self.filename:
                    print "Updating self.filename: ->%s<- (type: %s) with new name: ->%s<- (type: %s)" % (self.filename, type(self.filename), new_name, type(new_name))
                    self.filename = new_name

            #update paths if any are incomplete:
            # - updated drive_dir ?

            #not sure what this check accomplishes...
            #maybe it doesn't update drive_dir and base_dir if nothing
            #has changed
            #
            #but sometimes drive_dir was not set correctly to begin with
            #(includes base_dir)
            #
            #seems ok to always check
            #drive_dir_matches = False
            #if self.drive_dir and re.match(self.drive_dir, source_dir):
            #    drive_dir_matches = True

            #if not re.search(self.base_dir, source_dir):
            #    print "WARNING: could not find base_dir (%s) in source_dir (%s)" % (self.base_dir, source_dir)
            #else:


            #base_dir will only be set if it already exists in the loaded json
            #print self.base_dir
            if len(self.base_dir):
                if re.search(self.base_dir, source_dir):
                    base_len = len(self.base_dir) * -1
                    new_drive = source_dir[:base_len]

                    if self.drive_dir != new_drive:
                        #print "Updating self.drive_dir: ->%s<- (type: %s) to: ->%s<- (type: %s)" % (self.drive_dir, type(self.drive_dir), new_drive, type(new_drive))
                        pass

                    self.drive_dir = new_drive
                        
                else:
                    #base_dir didn't match our source_path
                    #this could happen in the case of copied content
                    #to people indexes
                    #update both in that case
                    #print "Updating self.drive_dir: ->%s<- (type: %s) to: ->%s<- (type: %s)" % (self.drive_dir, type(self.drive_dir), source_dir, type(source_dir))
                    self.base_dir = ''
                    self.drive_dir = source_dir


            else:
                if self.drive_dir != source_dir:
                    #print "Updating self.drive_dir: ->%s<- (type: %s) to: ->%s<- (type: %s)" % (self.drive_dir, type(self.drive_dir), source_dir, type(source_dir))
                    self.drive_dir = source_dir
                    

    #having trouble getting this:
    #going back to ids for now
    ## def __str__(self):
    ##     """
    ##     when cast to a string, probably want the first media file path
    ##     """
    ##     #return self.as_moment().render()
    ##     ## if len(self.media):
    ##     ##     return self.media[0]
    ##     ## else:
    ##     ##     return ""
    ##     return os.path.join(self.path, self.filename)



    def _seek_up(self, attribute='_filename'):
        """
        only look for attribute by going up
        ok to return None if no value is ultimately found
        """
        if hasattr(self, attribute) and getattr(self, attribute):
            return getattr(self, attribute)
        else:
            #print self.debug()
            if not (self.parent is None):
                return self.parent._seek_up(attribute)
            elif not (self.root is None) and (self.root != self):
                return self.root._seek_up(attribute)
            else:
                return None
            
    def _seek_down(self, attribute='_filename', depth_first=True):
        """
        only look for the specified attribute by searching down
        ok to return None if no attribute is ultimately found
        """

        #if we don't have the attribute or
        #if we have the attribute, but it doesn't have a value
        if ( (not hasattr(self, attribute)) or
             (hasattr(self, attribute) and (not getattr(self, attribute))) ):

            #keep looking:
            found_something = False
            index = 0
            while not found_something:
                if index < len(self.segments):
                    option = self.segments[index]._seek_down(attribute, depth_first)
                    if option:
                        found_something = True
                        return option
                    index += 1
                else:
                    return None
        
        elif hasattr(self, attribute):
            return getattr(self, attribute)
        else:
            #shouldn't get here:
            raise ValueError, "Unexpected condition"

    #TODO:
    #These are a bit like global variables for the Content tree structure
    #not sure if there is a better way to implement them

    def _get_filename(self):
        #search here
        if not (self._filename):
            option = self._seek_up('_filename')
            if not option:
                option = self._seek_down('_filename')
                if not option:
                    #print "Could not find filename anywhere"
                    return ''
                    #don't call self.debug() if raising an error!
                    #raise ValueError, "Could not find filename anywhere"
                
            return option
        else:
            return self._filename
            
    def _set_filename(self, name):
        self._filename = name            

    filename = property(_get_filename, _set_filename)

    def _get_json_source(self):
        #search here
        if not (self._json_source):
            option = self._seek_up('_json_source')
            if not option:
                #doesn't seem like it makes sense to seek_down with json_source
                #option = self._seek_down('_json_source')
                #if not option:

                #print "Could not find json_source above"
                return ''

            else:
                return option
        else:
            return self._json_source
            
    def _set_json_source(self, name):
        self._json_source = name            

    json_source = property(_get_json_source, _set_json_source)

    def _get_track_prefix(self):
        if not (self._track_prefix):
            option = self._seek_up('_track_prefix')
            if not option:
                option = self._seek_down('_track_prefix')
                if not option:
                    #print "Could not find track_prefix anywhere"
                    return ''
                
            return option
        else:
            return self._track_prefix
            
    def _set_track_prefix(self, name):
        self._track_prefix = name            

    track_prefix = property(_get_track_prefix, _set_track_prefix)

    def _get_path(self):
        """
        use self.drive_dir and self.base_dir to determine the current path
        
        this is a better way to quickly determine the current full path
        this is useful for calls to __repr__ and __str__
        
        Content object might not always be part of a Collection 
        or the Collection may not be loaded (e.g. in a Playlist)
        all we really need in this case is the collection base
        (the part of the path that changes due to storage shifts / mounts)
        
        previously, in Source objects, it was just .path
        but this can be brittle when drive locations change (as they often do)


        Segments (nested Content objects) complicate the issue some.
        Two options:
        - make sure all levels always have self.drive_dir and self.base_dir
          might not be able to rely on creator to do this
          and some levels may not have any media associated with it
          in which case it doesn't make much sense
          
        - a way to scan the levels for the closest viable path
          this is tricky since it might not be obvious which way to go
          (trace up, or dig down)
          and need to make sure no infinite recursion happens

        this version uses more generalized _seek_up and _seek_down methods
        """
        #search here
        if not (self.drive_dir):
            dd_option = self._seek_up('drive_dir')
            if not dd_option:
                dd_option = self._seek_down('drive_dir')
                if not dd_option:
                    #print "Incomplete drive_dir: %s (drive_dir).  Could not find drive_dir anywhere: %s" % (self.drive_dir, self.root.to_dict())
                    #return ''

                    #seems like if you're asking for a path
                    #and the parts aren't there, that's an error
                    raise ValueError, "Incomplete drive_dir: %s (drive_dir).  Could not find drive_dir anywhere: %s" % (self.drive_dir, self.root.to_dict())

            if not (self.base_dir):
                bd_option = self._seek_up('base_dir')
                if not bd_option:
                    bd_option = self._seek_down('base_dir')
                    if not bd_option:
                        #print "Incomplete base_dir: %s (base_dir).  Could not find base_dir anywhere: %s" % (self.base_dir, self.root.to_dict())
                        #return ''

                        #seems like if you're asking for a path
                        #and the parts aren't there, that's an error
                        raise ValueError, "Incomplete base_dir: %s (base_dir).  Could not find base_dir anywhere: %s" % (self.base_dir, self.root.to_dict())
            else:
                bd_option = self.base_dir

                
            return os.path.join(dd_option, bd_option)
        else:
            return os.path.join(self.drive_dir, self.base_dir)
        
    path = property(_get_path)
    #def _set_path(self, name):
    #    self.parse_name(name)
    #path = property(_get_path, _set_path)

    def add_segment(self, segment):
        """
        segment should already be initialized,
        everything except segments ids (unless previously generated)
        and being added to our segments,
        with parent and root updated accordingly
        """
        segment.parent = self
        #this should be set during Content.__init__
        #otherwise it is not carried all the way down the chain
        #segment.root = self.root
        
        if not segment.segment_id:
            #generate a new segment_id here
            #based on self.segment_id
            if not self.segment_id:
                new_id = str(self.next_segment_id)
            else:
                new_id = "%s_%s" % (self.segment_id, self.next_segment_id)
            self.next_segment_id += 1

            segment.segment_id = new_id
        
        self.segments.append(segment)

    def get_segment(self, segment_id):
        """
        parse through our segments (and those segment's segments, etc)
        to find the matching segement id
        """
        if not segment_id:
            return self
        else:
            id_parts = segment_id.split('_')
            path = []
            cur_id = ''
            cur_segment = self
            for part in id_parts:
                if not cur_id:
                    cur_id = part
                else:
                    cur_id = '_'.join( [cur_id, part] )
                path.append(cur_id)

                next_segment = None
                for segment in cur_segment.segments:
                    if segment.segment_id == cur_id:
                        next_segment = segment

                if next_segment is None:
                    raise ValueError, "Could not find segment_id: %s, in: %s" % (segment_id, self.to_dict())
                cur_segment = next_segment

            #print "found the following ids for segment path: %s" % path

            return cur_segment            

    def load(self, source=None, debug=False):
        """
        filename attribute should be unique
        this solves the issue with multiple files in the same directory
        """
        if source:
            #if it's a path, scan for json:
            #content = find_and_load_json(source)
            self.json_source = find_json(source)
            #json = find_json(source)
            content = load_json(self.json_source)
        else:
            content = self.content

        #if we're trying to create a new Content object from scratch,
        #we don't want to raise this error.
        #if not content:
        #    raise ValueError, "No Content!"

        if debug:
            print content

        if not isinstance(content, dict):
            #print "%s" % content
            print ""
            print content
            print self.json_source
            raise ValueError, "Unknown type of content: %s" % type(content)

        #start keeping track of ultimate source for this content
        #if it ends up as part of another list, this is the way to get back
        if content.has_key('json_source'):
            option = content['json_source']
            if self.json_source and self.json_source != option:
                #print "WARNING: over-writing old source."
                #print "keeping initial source: %s and skipping found source: %s" % (self.json_source, option)
                #print ""
                pass
            else:
                self.json_source = option
            del content['json_source']

        if content.has_key('timestamp'):
            self.timestamp = Timestamp(content['timestamp'])
            del content['timestamp']
        if content.has_key('date'):
            self.timestamp = Timestamp(content['date'])
            del content['date']
            
        if content.has_key('title'):
            self.title = content['title']
            del content['title']
            
        if content.has_key('description'):
            self.description = content['description']
            del content['description']
            
        if content.has_key('sites'):
            self.sites = content['sites']
            del content['sites']

        if content.has_key('image'):
            self.image = content['image']
            del content['image']

        if content.has_key('people'):
            for person in content['people']:
                self.people.append(to_tag(person))
            del content['people']
            
        if content.has_key('tags'):
            for tag in content['tags']:
                self.tags.append(to_tag(tag))
            del content['tags']

        if content.has_key('tracks'):
            for title in content['tracks']:
                self.titles.append(title)
            del content['tracks']

        if content.has_key('status'):
            self.status = content['status']
            del content['status']

        if content.has_key('segment_id'):
            self.segment_id = content['segment_id']
            del content['segment_id']

        if content.has_key('next_segment_id'):
            self.next_segment_id = content['next_segment_id']
            del content['next_segment_id']

        if content.has_key('track_prefix'):
            self.track_prefix = content['track_prefix']
            del content['track_prefix']

        if content.has_key('marks'):
            ml = MarkList()
            ml.from_tuples(content['marks'])
            ## for mark in content['marks']:
            ##     self.marks.append(to_mark(mark))
            self.marks = ml
            del content['marks']

        if content.has_key('segments'):
            #segments = []
            for seg in content['segments']:
                sub_c = Content(content=seg, root=self.root)
                self.add_segment(sub_c)

                #these steps are handled by self.add_segment now:
                #sub_c.parent = self
                #sub_c.root = self.root
                #segments.append(sub_c)
            #self.segments = segments
            del content['segments']

        if content.has_key('start'):
            mark = Mark()
            mark.seconds = int(content['start'])
            self.start = mark
            del content['start']

        if content.has_key('end'):
            mark = Mark()
            mark.seconds = int(content['end'])
            self.end = mark
            del content['end']

        if content.has_key('history'):
            history = content['history']
            l = Log()
            l.from_string(history)

            #shouldn't need to add any tags here
            #entries = l.to_entries(add_tags)
            entries = l.to_entries()
            #print "%s entries loaded from file" % len(entries)
            #print "%s entries in self before merging in entries" % len(self)
            journal = Journal()
            journal.update_many(entries)
            #print "%s entries in self after merging in entries" % len(self)

            #if l.has_entries:
            #found_entries = len(entries)

            l.close()

            #return found_entries
            self.history = journal
            
            del content['history']


        #deprecated: root is ambiguous here
        #will continue to load for older jsons
        if content.has_key('root'):
            self.base_dir = content['root']
            del content['root']
        if content.has_key('content_base'):
            self.base_dir = content['content_base']
            del content['content_base']

        if content.has_key('drive_dir'):
            self.drive_dir = content['drive_dir']
            del content['drive_dir']

        if content.has_key('media'):
            self.media = content['media']
            del content['media']

        #no path here! filename only!
        if content.has_key('filename'):
            self.filename = content['filename']
            del content['filename']

        if content.has_key('hash'):
            self.hash = content['hash']
            del content['hash']


        #deprecated... use self.sites instead
        #site is only loaded for legacy json files...
        #loaded into self.sites
        #not saved
        if content.has_key('site'):
            self.sites.append(content['site'])
            del content['site']



        if debug:
            print "didn't convert the following keys for content: %s" % content.keys()
            print content
            print

        #keep everything left over so we have it later for storing
        self.remainder = content

        ## if debug:
        ##     print "Could not process the following when loading Content:"
        ##     print self.remainder


    def to_dict(self, include_empty=False):
        """
        the order specified here is generally the order that gets printed(?)
        (maybe not)
        """
        #deep copy was crashing on pretty small track lists (<150 in length)
        #using a manual alternative instead
        #snapshot = copy.deepcopy(self.remainder)

        #print self.remainder
        snapshot = {}
        for key, value in self.remainder.items():
            if isinstance(value, list):
                snapshot[key] = value[:]
            elif isinstance(value, str) or isinstance(value, unicode):
                snapshot[key] = value
            else:
                #print "deep copy for type: %s : %s" % (type(value), value)
                snapshot[key] = copy.deepcopy(value)
        #print ""
        #print snapshot
        #exit()

        #check to make sure we have values...
        #no need to clutter up json with empty values
        if self.tags or include_empty:
            snapshot['tags'] = self.tags
        if self.people or include_empty:
            snapshot['people'] = self.people
        if self.sites or include_empty:
            snapshot['sites'] = self.sites
        if self.image or include_empty:
            snapshot['image'] = self.image
        if self.description or include_empty:
            snapshot['description'] = self.description
        if self.title or include_empty:
            snapshot['title'] = self.title
        if self.timestamp or include_empty:
            if self.timestamp: 
                snapshot['timestamp'] = self.timestamp.compact()
            else:
                snapshot['timestamp'] = ''

        if self.status or include_empty:
            snapshot['status'] = self.status

        #segments don't need content_base to be set if root has it:
        if self.base_dir or include_empty:
            snapshot['content_base'] = self.base_dir
        if self.media or include_empty:
            snapshot['media'] = self.media
        if self.filename or include_empty:
            snapshot['filename'] = self.filename
        if self.hash or include_empty:
            snapshot['hash'] = self.hash
        if self.drive_dir or include_empty:
            snapshot['drive_dir'] = self.drive_dir

        if self.json_source or include_empty:
            snapshot['json_source'] = self.json_source
            
        if self.start.total_seconds() or include_empty:
            snapshot['start'] = self.start.total_seconds()

        if self.end:
            snapshot['end'] = self.end.total_seconds()
        elif include_empty:
            #shouldn't need this
            pass

        if self.segment_id or include_empty:
            snapshot['segment_id'] = self.segment_id

        if self.next_segment_id != 1 or include_empty:
            snapshot['next_segment_id'] = self.next_segment_id

        if self.track_prefix or include_empty:
            snapshot['track_prefix'] = self.track_prefix


        #keeping this consistent with old format:
        if self.titles or include_empty:
            snapshot['tracks'] = self.titles

        #marks = []
        #for m in self.marks:
        #    marks.append(m.total_seconds())
        marks = self.marks.to_tuples()
        if marks or include_empty:
            snapshot['marks'] = marks

        segments = []
        for segment in self.segments:
            segments.append(segment.to_dict())
        if segments or include_empty:
            snapshot['segments'] = segments

        if self.history or include_empty:
            l = Log()
            l.from_entries(self.history.sort())
            snapshot['history'] = l.to_string()
            l.close()
            
            #snapshot['history'] = self.history

        #root can sometimes be full path to a specific drive
        #here we use it as a relative path, so it's the same as base
        #snapshot['content_root'] = self.root

        return snapshot

    def save(self, destination=None):
        """
        now that self.json_source is a property
        that automatically seeks up for the correct file name,
        we need to make sure the a sub segment of a content
        does not clobber the main content object data stored in the file
        by only saving the segment data to json_source

        should be *VERY* careful if a child segment is ever initialized
        outside and independent of the main Content that contains it...
        if no root is set, then it could over write parent Content data
        """
        if self.root != self:
            self.root.save(destination)
        else:
            if not destination:
                if self.json_source:
                    destination = self.json_source
                else:
                    raise ValueError, "unknown destination: %s and unknown source: %s" % (destination, self.json_source)

            d = self.to_dict()

            if d.has_key('json_source') and d['json_source'] != destination:
                print "UPDATING json_source from: %s to %s" % (d['json_source'], destination)
                d['json_source'] = destination

            save_json(destination, d)

    def find_extension(self, search_for, location=None, ignores=[], debug=False):
        """
        search for should be a regular expression, like:
        '.*mp4$'

        ignores is a list of regular expressions to exclude

        only look for a specific type of content
        """
        if location is None:
            location = self.path

        search = "%s$" % search_for
        #print "searching using: %s" % search
        media_check = re.compile(search)
        options = []
        
        if location and os.path.exists(location) and os.path.isdir(location):
            if debug:
                print "Drive Available!: %s" % disk
            for root,dirs,files in os.walk(location):
                for f in files:
                    ignore = False
                    for i in ignores:
                        #want to make sure extension shows up at the end of the file:
                        if re.search(i, f):
                            ignore = True
                    if not ignore:
                        media = os.path.join(root, f)
                        if media_check.search(f):
                            options.append(media)
        return options

    def find_image(self, ignores=[], debug=False):
        images = self.find_media(kind="Image", relative=False, debug=debug)
        if images:
            #clear out anything that should be removed first
            for ignore in ignores:
                for image in images[:]:
                    #this is a 1:1 match:
                    #if str(image) == str(ignore):
                    #regular expression might be better here:
                    if re.search(ignore, str(image)):
                        if debug:
                            print "Removing: %s" % image
                        images.remove(image)
                        
            if debug:
                print images
            self.image = images[0]
        else:
            self.image = ''
        
    def find_media(self, location=None, kind="Movie", relative=True,
                   ignores=[], limit_by_name=False, debug=False):
        """
        ideally we just use self.path as the location to look in
        might be nice to pass it in though

        using moments.path.Path.type() here
        kind can be either "Movie", "Image", or "Sound"

        relative will determine if self.drive_dir is included in prefix...
        usually it's better not to include that
        """
        if location is None:
            location = self.path
        
        extensions = {}

        if debug:
            print "Looking at Location: %s" % location

        if location and os.path.exists(location) and os.path.isdir(location):
            if debug: 
                print "Location Available!: %s" % location
            for root,dirs,files in os.walk(location):
                for f in files:
                    ignore = False
                    for i in ignores:
                        if re.search(i, f):
                            ignore = True
                    if not ignore:
                        media = os.path.join(root, f)
                        mpath = Path(media)
                        #if debug:
                        #    print "looking at: %s" % media
                        if mpath.type() == kind:
                            if debug:
                                print "Found %s: %s" % (kind, f)
                            if extensions.has_key(mpath.extension):
                                extensions[mpath.extension].append(media)
                            else:
                                extensions[mpath.extension] = [ media ]
                        else:
                            #this can be *very* verbose...
                            #probably want to keep it commented out,
                            #even for debugging!
                            ## if debug:
                            ##     #print "Skipping %s: %s" % (mpath.type(), media)
                            ##     print "Skipping %s: %s" % (mpath.type(), f)
                            pass

        #if debug:
        #    print "found the following:"

        if len(extensions.keys()) > 1:
            #more than one extension...
            #check for duplicate versions of the same file

            #could order some how... just sorting for now
            filenames = []
            sorted_keys = extensions.keys()
            sorted_keys.sort()
            print "SORTED KEYS: %s" % sorted_keys
            for ext in sorted_keys:
                for media in extensions[ext][:]:
                    mpath = Path(media)
                    if mpath.name in filenames:
                        extensions[ext].remove(media)
                        print "REMOVING DUPE: %s" % media
                    else:
                        filenames.append(mpath.name)
                    
                

        combined = []
        for key in extensions.keys():
            combined.extend(extensions[key])

            if debug:
                print "%s %ss" % (len(extensions[key]), key)

        if debug:
            print "Found %s media files" % (len(combined))
            #print combined


        if debug:
            print "LIMIT BY NAME: %s, FILENAME: %s" % (limit_by_name, self.filename)
        if limit_by_name and self.filename:
            if debug:
                print "using filename: %s to filter list" % self.filename

            accepted = []
            for item in combined:
                if re.search(self.filename, item):
                    accepted.append(item)

            if debug:
                print "The following items match: %s" % accepted
            combined = accepted

        shorts = []
        if relative:
            for item in combined:
                path = Path(item)
                shorts.append(path.to_relative(self.drive_dir))

            combined = shorts
            
        #at this point, could store result
        #or could look for sizes
        #or could generate generic summary files based on what we do know

        return combined

    def check_new(self):
        """
        look at our own status
        and all status fields for any segments contained within
        if all are new, return True
        if any are not new, return False
        """
        all_new = True
        if self.status != 'new':
            all_new = False
            return all_new
        else:
            for segment in self.segments:
                all_new = segment.check_new()
                if not all_new:
                    return all_new
                #otherwise keep looking
                
        #if we make it here, it should be new
        assert all_new == True
        return all_new        

    def make_hash(self, filename=None):
        """
        via this excellent thread:
        http://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-python        
        """

        if filename:
            self.filename = filename

        path = os.path.join(self.path, self.filename)

        if not os.path.exists(path) or os.path.isdir(path):
            print "Skipping Hash: File not found: %s" % path
            return None
        else:
            md5 = hashlib.md5()
            with open(path, 'rb') as f: 
                for chunk in iter(lambda: f.read(8192), b''): 
                     md5.update(chunk)

            self.hash = md5.hexdigest()
            return self.hash

    def equal(self, content):
        """
        take another content object

        TODO: test different approaches to find optimal way for comparing
        if two content objects are the same, even if they're loaded from
        different sources

        ideally, the hash was computed at some point and we can just use that
        """
        if not self.hash or not content.hash:
            if not self.filename or not content.filename:
                print self.debug()
                print content.debug()
                #may not be able to calculate hash if media file is not local:
                #raise ValueError, "Cannot compare unless hash / filename exists"
                print "Cannot compare unless hash / filename exists"
                #assume they're not equal
                return False
            else:
                if self.filename == content.filename:
                    return True
                else:
                    return False
        else:
            #could just return the result of comparison directly,
            #but this is a bit more readable IMO
            if self.hash == content.hash:
                return True
            else:
                return False

    def update_dimensions(self, options, force=False, debug=False):
        """
        compare options with our internal list of media
        
        options is a list of paths to media

        #two common ways to generate them:
        #this will not distinguish between different file formats
        options = self.find_media()

        #if you need to do that:
        #options = self.find_extension()
        """
        if debug:
            print "before looking at cache, found: %s items" % len(options)

        matches = []

        if not force:
            for item in options[:]:
                for m in self.media:
                    #if the path matches,
                    #media has a size field,
                    #and the size has a value
                    #then no need to rescan. remove it.
                    if item == m[0] and (len(m) > 2) and (m[1]):
                        print "skipping: %s because it matched %s" % (item, m)
                        matches.append(m)
                        if item in options:
                            options.remove(item)
        
        if debug:
            print "after looking at cache, matched: %s items" % len(matches)
            print "still need to find: %s new items" % len(options)

        for item in options:
            #dimensions = get_media_dimensions(item)
            dimensions, duration = get_media_properties(item)
            self.end = Mark(seconds=duration)
            #print self.end
            if debug:
                print "FOUND DIMENSIONS: %s" % dimensions
            filesize = os.path.getsize(item)
            if debug:
                print "FOUND FILE SIZE: %s" % filesize
            matches.append( [item, dimensions, filesize] )

        self.media = matches

        return self.media

    def as_moment(self, use_file_created=True, new_entry=False):
        moment = Moment()
        if self.entry and not new_entry:
            moment.tags = self.entry.tags
            moment.created = self.entry.created
        elif new_entry:
            #want to keep the file the same, but nothing else
            moment.tags = Tags()
            
        else:
            moment.tags = Tags()
            
            created = self.path.created()
            if created and use_file_created:
                moment.created = created
                #otherwise we just want to stick with 'now' default of init

        if self.jumps:
            moment.data = "# -sl %s %s" % (self.jumps.to_comma(), self.path)
        else:
            moment.data = str(self.path)


        return moment

    def debug(self, indent=0, recurse=True):
        """
        make a printable representation of self that is easy to read and debug
        """
        result = ""
        

        #these require that the string representation is working
        result += ''.ljust(indent) + str(self) + '\n'
        result += ''.ljust(indent) + 'parent: %s\n' % self.parent
        result += ''.ljust(indent) + 'root: %s\n' % self.root

        if self.base_dir:
            result += ''.ljust(indent) + 'base_dir: %s\n' % self.base_dir
        if self.drive_dir:
            result += ''.ljust(indent) + 'drive_dir: %s\n' % self.drive_dir
        if self.filename:
            result += ''.ljust(indent) + 'filename: %s\n' % self.filename
        if self.media:
            result += ''.ljust(indent) + 'media: %s\n' % self.media
            
        if self.start:
            result += ''.ljust(indent) + 'start: %s\n' % self.start.total_seconds()
        else:
            result += ''.ljust(indent) + 'start: %s\n' % self.start

        if self.end:
            result += ''.ljust(indent) + 'end: %s\n' % self.end.total_seconds()
        else:
            result += ''.ljust(indent) + 'end: %s\n' % self.end

        if self.segment_id:
            result += ''.ljust(indent) + 'segment_id: %s\n' % self.segment_id
        if self.next_segment_id:
            result += ''.ljust(indent) + 'next_segment_id: %s\n' % self.next_segment_id
        if self.track_prefix:
            result += ''.ljust(indent) + 'track_prefix: %s\n' % self.track_prefix

        if self.tags:
            result += ''.ljust(indent) + 'tags: %s\n' % self.tags
        if self.people:
            result += ''.ljust(indent) + 'people: %s\n' % self.people
        if self.sites:
            result += ''.ljust(indent) + 'sites: %s\n' % self.sites
        if self.description:
            result += ''.ljust(indent) + 'description: %s\n' % self.description
        if self.title:
            result += ''.ljust(indent) + 'title: %s\n' % self.title

        if self.timestamp:
            result += ''.ljust(indent) + 'timestamp: %s\n' % self.timestamp.compact()
        else:
            result += ''.ljust(indent) + 'timestamp: %s\n' % self.timestamp

        if self.status:
            result += ''.ljust(indent) + 'status: %s\n' % self.status

        if self.hash:
            result += ''.ljust(indent) + 'hash: %s\n' % self.hash

        if self.history:
            result += ''.ljust(indent) + 'history: %s\n' % self.history

        #marks = self.marks.to_tuples()
        #if marks:
        #    snapshot['marks'] = marks

        result += ''.ljust(indent) + 'segments:\n'
        if recurse:
            for segment in self.segments:
                result += segment.debug(indent+10)

        result += '\n'

        #snapshot = copy.deepcopy(self.remainder)

        #print result
        return result

