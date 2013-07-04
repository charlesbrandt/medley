"""
Content related objects.

What best describes this object? Going with Content... other options were:
Thing, Item, Medium, Source, 

These are too specific:
Song, Podcast, Album, Image, Book, Movie, Scene, 

"""
import os, re, copy

from helpers import save_json, get_media_dimensions, find_json, load_json

from moments.path import Path
from moments.timestamp import Timestamp
from moments.tag import to_tag


class Mark(object):
    """
    position time associated with a specific media file

    AKA:
    jump, bookmark, markpoint/MarkPoint
    """
    def __init__(self, tag='', position=0, source=None, length=None, created=None, bytes=None, title=""):
        #*2013.06.16 08:24:49 
        #not sure how tag and title differ... (see note below)
        #also what about 'name' or 'description' (better in a segment)

        #tag is a user specified tag or category ('work', 'chill', 'other')
        self.tag = tag
        
        #once we've determined the real title of the mark location:
        #self.title = title
        #this is better represented in a segment instead of a mark
        
        #in milliseconds
        self.position = position
        self.source = source

        #only used in mortplayer
        #assuming length should be ms?
        self.length = length
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
        return int(self.position) / 1000

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
        return (self.total_seconds, new_tag)

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
    """
    def __init__(self, comma='', items=[]):
        super(MarkList, self).__init__()
        
        #self.extend(items)
        for item in items:
            assert isinstance(item, Mark)
            self.append(item)

        if comma:
            self.from_comma(comma)

    def to_tuples(self):

        result = []
        for mark in self:
            result.append(mark.as_tuple())
        return result

    def from_tuples(self, tuples):
        for t in tuples:
            mark = Mark()
            mark.seconds = t[0]
            mark.tags = t[1]
            self.append(mark)
        
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

    this is a place to draw those together
    """
    def __init__(self, source=None, content={}, debug=False):
        """
        few different ways to initialize an item of content:

          - can pass a specific media file as source,
            then look for meta data in a local json file

          - can pass a raw dictionary representation of the content meta data
            (often loaded from a json file)

          - can pass a root where a meta data file is located

        """
        #the root location relative to collection base
        #self.root = root

        #everything leading up to the base_dir 
        #this is the start of the collection (collection root path)
        self.drive_dir = ''

        #aka path from collection root
        #relative path for other content
        self.base_dir = ''

        
        #the default filename associated with the content
        self.filename = ''

        # store a list of local media files,
        # along with dimensions if we calculate those
        # (could be other properties of the media to store)
        #
        # if there is more than one media file, media[0] is the default
        #
        # if there are multiple media files that comprise a single Content
        # object, those might be better represented in self.segments
        self.media = []



        self.title = ''
        self.description = ''
        #when content was created or published (according to publisher)
        self.timestamp = None

        self.added = ''
        self.visited = ''

        self.sites = []

        self.people = []
        self.tags = []

        self.marks = MarkList()

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
        self.history = ""


        #these attributes are generated and assigned later
        #no need to store them with a json file / dict

        #these should be used for segements and sub-segments
        #in order to load and save changes to segments
        #that are located out of context from original Content root
        self.parent = None
        self.root = self



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
            # json file to save and load from
            #this is the best way to initialize previous Content object:
            #ok to include full path here...
            self.json_source = find_json(source)
            #make sure something was found:
            if self.json_source:
                self.load(self.json_source)

            #now go back and update paths if any are incomplete,
            #or check if what is stored in file is out of date
            #based on json_source location ...

            if self.json_source != source:
                #must have been passed something besides a json path
                #do some checks to see if there is anything we can use:
                # - updated filename
                new_name = os.path.basename(source)
                if new_name and new_name != self.filename:
                    print "Updating self.filename: %s with new name: %s" % (
                        self.filename, new_name)
                    self.filename = new_name

            # - updated drive_dir ?
            source_dir = os.path.dirname(self.json_source)

            drive_dir_matches = False
            if self.drive_dir and re.match(self.drive_dir, source_dir):
                drive_dir_matches = True

            if not re.search(self.base_dir, source_dir):
                print "WARNING: could not find base_dir (%s) in source_dir (%s)" % (self.base_dir, source_dir)
            else:
                #must have self.base_dir in source_dir
                if not drive_dir_matches:
                    base_len = len(self.base_dir) * -1
                    new_drive = source_dir[:base_len]
                    print "Updating self.drive_dir from: %s to: %s" % (self.drive_dir, new_drive)
                    self.drive_dir = new_drive


        #is it even necessary to link back to the containing list/collection?
        #can re-enable if there is a usecase
        #self.collection = ''
        #what about playlists? way to generalize here?



    def _get_path(self):
        """
        use self.drive_dir and self.base_dir to determine the current path
        
        this better way to quickly determine the current full path
        this is useful for calls to __repr__ and __str__
        
        Content object might not always be part of a Collection 
        or the Collection may not be loaded (e.g. in a Playlist)
        all we really need in this case is the collection base
        (the part of the path that changes due to storage shifts / mounts)
        
        previously, in Source objects, it was just .path
        but this can be brittle when drive locations change (as they do)
        """
        return os.path.join(self.drive_dir, self.base_dir)

    path = property(_get_path)
    #def _set_path(self, name):
    #    self.parse_name(name)
    #path = property(_get_path, _set_path)

    def __str__(self):
        """
        when cast to a string, probably want the first media file path
        """
        #return self.as_moment().render()
        ## if len(self.media):
        ##     return self.media[0]
        ## else:
        ##     return ""
        return os.path.join(self.path, self.filename)

    def add_segment(self, segment):
        """
        segment should already be initialized,
        everything except segments ids (unless previously generated)
        and being added to our segments,
        with parent and root updated accordingly
        """
        segment.parent = self
        segment.root = self.root
        
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

        if not content:
            raise ValueError, "No Content!"

        if debug:
            print content

        if not isinstance(content, dict):
            #print "%s" % content
            raise ValueError, "Unknown type of content: %s" % type(content)

        if content.has_key('timestamp'):
            self.timestamp = Timestamp(content['timestamp'])
            del content['timestamp']
            
        if content.has_key('title'):
            self.title = content['title']
            del content['title']
            
        if content.has_key('description'):
            self.description = content['description']
            del content['description']
            
        if content.has_key('sites'):
            self.sites = content['sites']
            del content['sites']

        if content.has_key('people'):
            for person in content['people']:
                self.people.append(to_tag(person))
            del content['people']
            
        if content.has_key('tags'):
            for tag in content['tags']:
                self.tags.append(to_tag(tag))
            del content['tags']

        if content.has_key('status'):
            self.status = content['status']
            del content['status']

        if content.has_key('segment_id'):
            self.segment_id = content['segment_id']
            del content['segment_id']

        if content.has_key('next_segment_id'):
            self.next_segment_id = content['next_segment_id']
            del content['next_segment_id']

        if content.has_key('marks'):
            ml = MarkList()
            ml.from_tuples(content['marks'])
            ## for mark in content['marks']:
            ##     self.marks.append(to_mark(mark))
            self.marks = ml
            del content['marks']

        if content.has_key('segments'):
            segments = []
            for seg in content['segments']:
                sub_c = Content(content=seg)
                self.add_segment(sub_c)

                #these steps are handled by self.add_segment now:
                #sub_c.parent = self
                #sub_c.root = self.root
                #segments.append(sub_c)
            self.segments = segments
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
            self.history = content['history']
            del content['history']


        #deprecated: root is ambiguous here
        #will continue to load for older jsons
        if content.has_key('root'):
            self.base_dir = content['root']
            del content['root']
        if content.has_key('content_base'):
            self.base_dir = content['content_base']
            del content['content_base']

        if content.has_key('media'):
            self.media = content['media']
            del content['media']

        #no path here! filename only!
        if content.has_key('filename'):
            self.filename = content['filename']
            del content['filename']


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


    def to_dict(self):
        """
        the order specified here is generally the order that gets printed(?)
        (maybe not)
        """
        snapshot = copy.deepcopy(self.remainder)
        #check to make sure we have values...
        #no need to clutter up json with empty values
        if self.tags:
            snapshot['tags'] = self.tags
        if self.people:
            snapshot['people'] = self.people
        if self.sites:
            snapshot['sites'] = self.sites
        if self.description:
            snapshot['description'] = self.description
        if self.title:
            snapshot['title'] = self.title
        if self.timestamp:
            snapshot['timestamp'] = self.timestamp.compact()

        if self.status:
            snapshot['status'] = self.status

        #segments don't need content_base to be set if root has it:
        if self.base_dir:
            snapshot['content_base'] = self.base_dir
        if self.media:
            snapshot['media'] = self.media
        if self.filename:
            snapshot['filename'] = self.filename
        if self.drive_dir:
            snapshot['drive_dir'] = self.drive_dir

        if self.start.total_seconds():
            snapshot['start'] = self.start.total_seconds()

        if self.end:
            snapshot['end'] = self.end.total_seconds()

        if self.segment_id:
            snapshot['segment_id'] = self.segment_id

        if self.next_segment_id != 1:
            snapshot['next_segment_id'] = self.next_segment_id

        #marks = []
        #for m in self.marks:
        #    marks.append(m.total_seconds())
        marks = self.marks.to_tuples()
        if marks:
            snapshot['marks'] = marks

        segments = []
        for segment in self.segments:
            segments.append(segment.to_dict())
        if segments:
            snapshot['segments'] = segments

        if self.history:
            snapshot['history'] = self.history

        #root can sometimes be full path to a specific drive
        #here we use it as a relative path, so it's the same as base
        #snapshot['content_root'] = self.root

        return snapshot

    def save(self, destination=None):
        if not destination:
            if self.json_source:
                destination = self.json_source
            else:
                raise ValueError, "unknown destination: %s and unknown source: %s" % (destination, self.json_source)

        d = self.to_dict()

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

        media_check = re.compile(search_for)
        options = []
        
        if location and os.path.exists(location) and os.path.isdir(location):
            if debug:
                print "Drive Available!: %s" % disk
            for root,dirs,files in os.walk(location):
                for f in files:
                    ignore = False
                    for i in ignores:
                        if re.search(i, f):
                            ignore = True
                    if not ignore:
                        media = os.path.join(root, f)
                        if media_check.search(f):
                            options.append(media)
        return options

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

        if debug:
            print "found the following:"

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
                    if item == m[0] and (len(m) > 1) and (m[1]):
                        print "skipping: %s because it matched %s" % (item, m)
                        matches.append(m)
                        if item in options:
                            options.remove(item)
        
        if debug:
            print "after looking at cache, matched: %s items" % len(matches)
            print "still need to find: %s new items" % len(options)

        for item in options:
            size = get_media_dimensions(item)
            if debug:
                print "FOUND SIZE: %s" % size
            matches.append( [item, size] )

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


