"""
what best describes this object?
??? Content, Thing, Item, Medium, Source, 

these are too specific:
Song, Podcast, Album, Image, Book, Movie, Scene, 

"""
import os, re, copy

from helpers import find_and_load_json, save_json, get_media_dimensions

from moments.path import Path
from moments.timestamp import Timestamp
from moments.tag import to_tag


class Mark(object):
    """
    position time associated with a specific media file

    AKA:
    jump, bookmark, markpoint/MarkPoint
    """
    def __init__(self, tag, position, source, length=None, created=None, bytes=None, title=""):
        #*2013.06.16 08:24:49 
        #not sure how the following 2 differ:
        #also what about 'name' or 'description'
        self.tag = tag
        #once we've determined the real title of the mark location:
        self.title = title
        

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
        return "%s, %s, %s, %s\n" % (self.position, self.tag, self.title, self.source)

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


# aka Marks, or MarkPoints
#class Jumps(PositionList):
class MarkPoints(list):
    """
    object for keeping track of a list of Marks
    and comparing one list to anther for easier merging 
    """
    def __init__(self, comma='', items=[]):
        #Items.__init__(self, items)
        self.extend(items)
        #we don't want to loop over jumps
        self._position.loop = False
        if comma:
            self.from_comma(comma)
        
    def from_comma(self, source):
        """
        split a comma separated string into jumps
        """
        temps = source.split(',')
        for j in temps:
            try:
                self.append(int(j))
            except:
                print "could not convert %s to int from: %s" % (j, source)
        return self
    
    def to_comma(self):
        """
        combine self into a comma separated string
        """
        temp = []
        for j in self:
            if j not in temp:
                temp.append(str(j))
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



#aka Section
class Segment(object):
    """
    use a start Mark and an end Mark
    to designate a distinct section of a piece of content
    """
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end

        #should use the same naming scheme as a Mark for this attribute:
        if self.start:
            self.title = start.title
        else:
            self.title = ''


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
    def __init__(self, source=None, content={}, root='', debug=False):
        """
        few different ways to initialize an item of content:

          - can pass a specific media file as source,
            then look for meta data in a local json file

          - can pass a raw dictionary representation of the content meta data
            (often loaded from a json file)

          - can pass a root where a meta data file is located

        """
        #TODO:
        #need a better way to quickly determine the current full path
        #for calls to __repr__
        #Content object might not always be part of a Collection 
        #or the Collection may not be loaded (e.g. in a Playlist)
        #all we really need in this case is the collection base
        #(the part of the path that changes due to storage shifts / mounts)
        #
        #previously, in Source objects, it was just .path
        #but this can be brittle when drive locations change (as they do)

        self.collection = ''
        #the root location relative to collection base
        self.root = root
        
        # json file to save and load from?
        # maybe rename to json_source?
        self.json_file = source

        #the default filename associated with the content
        self.filename = ''

        # store a list of local media files,
        # along with dimensions if we calculate those
        # (could be other properties of the media to store)
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

        #TODO:
        #allow marks and segments to be saved and loaded with json:
        self.marks = []
        self.segments = []

        # there are many different states that a piece of content could be in
        # depending on the process being used to parse 
        self.complete = False
        #TODO:
        #instead of complete, use a more general status field
        #can be customized based on process used to add/update meta data
        self.status = 'new'

        self.remainder = {}

        #TODO:
        #keep a log of when actions happened:
        #used to do this with Moment logs to track media plays
        self.history = ""

        #what was passed in for manual initialization:
        #store this for subsequent call to load:
        self.content = content

    def __str__(self):
        """
        when cast to a string, probably want the first media file path
        """
        #return self.as_moment().render()
        if len(self.media):
            return self.media[0]
        else:
            return ""

    def load(self, source=None, debug=False):
        """
        filename attribute should be unique
        this solves the issue with multiple files in the same directory
        """
        if source:
            #if it's a path, scan for json:
            content = find_and_load_json(source)
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
            
        if content.has_key('content_base'):
            self.root = content['content_base']
            del content['content_base']

        if content.has_key('media'):
            self.media = content['media']
            del content['media']

        #no path here! filename only!
        if content.has_key('filename'):
            self.filename = content['filename']
            del content['filename']

        if content.has_key('sites'):
            self.sites = content['sites']
            del content['sites']
            
        if content.has_key('site'):
            self.sites.append(content['site'])
            del content['site']

        if content.has_key('people'):
            for person in content['people']:
                self.people.append(to_tag(person))
            del content['people']
            
        if content.has_key('tags'):
            for tag in content['tags']:
                self.tags.append(to_tag(tag))
            del content['tags']

        if debug:
            print "didn't convert the following keys for content: %s" % content.keys()
            print content
            print

        #keep everything left over so we have it later for storing
        self.remainder = content

        if debug:
            print "Could not process the following when loading Content:"
            print self.remainder


    def to_dict(self):
        snapshot = copy.deepcopy(self.remainder)
        snapshot['tags'] = self.tags
        snapshot['people'] = self.people
        snapshot['sites'] = self.sites
        snapshot['description'] = self.description
        snapshot['title'] = self.title
        if self.timestamp:
            snapshot['timestamp'] = self.timestamp.compact()
            
        #root can sometimes be full path to a specific drive
        #here we use it as a relative path, so it's the same as base
        #snapshot['content_root'] = self.root
        snapshot['content_base'] = self.root
        snapshot['complete'] = self.complete
        snapshot['media'] = self.media
        snapshot['filename'] = self.filename
        return snapshot

    def save(self, destination=None):
        if not destination:
            if self.json_file:
                destination = self.json_file
            else:
                raise ValueError, "unknown destination: %s and unknown source: %s" % (destination, self.json_file)

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
            location = self.root

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

    def find_media(self, location=None, kind="Movie", ignores=[], limit_by_name=False, debug=False):
        """
        ideally we just use self.root as the location to look in
        might be nice to pass it in though

        using moments.path.Path.type() here
        kind can be either "Movie", "Image", or "Sound"
        """
        if location is None:
            location = self.root
        
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


##     def find_media(self, location, search_for, ignores=[], debug=False):
##         """
##         search for should be a regular expression, like:
##         '.*mp4$'

##         ignores is a list of regular expressions to exclude
##         """
##         media_check = re.compile(search_for)
##         alternate = re.compile('.*\.wmv')
##         options = []
##         alts = []
##         if self.root:
##             path = os.path.join(location, self.root)
##             if os.path.isdir(path):
##                 for root,dirs,files in os.walk(path):
##                     for f in files:
##                         ignore = False
##                         for i in ignores:
##                             if re.search(i, f):
##                                 ignore = True
##                         if not ignore:
##                             media = os.path.join(root, f)
##                             if media_check.search(f):
##                                 options.append(media)
##                             if alternate.search(f):
##                                 alts.append(media)

## # original version stopped here:
## ##         if not len(options) and len(alts):
## ##             return alts
## ##         else:
## ##             return options

##         if not len(options) and len(alts):
##             checking = alts
##         else:
##             checking = options

##         if debug:
##             print "before looking at cache, found: %s items" % len(checking)

##         matches = []
##         for item in checking[:]:
##             for m in self.media:
##                 if item == m[0]:
##                     matches.append(m)
##                     checking.remove(item)

##         if debug:
##             print "after looking at cache, matched: %s items" % len(matches)
##             print "still need to find: %s new items" % len(checking)

##         for item in checking:
##             size = get_media_dimensions(item)
##             matches.append( [item, size] )

##         self.media = matches

##         return self.media
            
