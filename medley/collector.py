"""
Main objects needed for sorting collections.

Collection and Content may need to be customized for the specific type of colleciton in use. 


*2012.09.20 10:39:39
refactoring Scenes to Collection
refactoring Scene to Content
                
what best describes this object?
??? Content, Thing, Item, Medium, Source, 
these are too specific:
Song, Podcast, Album, Image, Book, Movie, Scene, 

"""
import os, re, logging

from helpers import find_and_load_json, load_json, save_json

from moments.path import Path, check_ignore
from moments.timestamp import Timestamp

from yapsy.PluginManager import PluginManager

class Content(object):
    """
    class to hold details of a particular piece of content (media)

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

          - can pass a root where a meta data file is located

          - can pass a raw dictionary representation of the content meta data
            (often loaded from a json file)

        """
        self.collection = ''
        self.root = root
        
        self.title = ''
        self.description = ''
        #when content was created or published (according to publisher)
        self.timestamp = ''

        self.added = ''
        self.visited = ''

        self.sites = []

        self.people = []
        self.tags = []

        # json file to save and load from?
        self.source = source

        # store a list of local media files,
        # along with dimensions if we calculate those
        # (could be other properties of the media to store)
        self.media = []

        # there are many different states that a piece of content could be in
        # depending on the process being used to parse 
        self.complete = False


    def load(self, json):
        if source:
            #if it's a path, scan for json:
            content = find_and_load_json(source)

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
            
        if content.has_key('media'):
            self.media = content['media']
            del content['media']
            

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

    def to_dict(self):
        snapshot = copy.deepcopy(self.remainder)
        snapshot['tags'] = self.tags
        snapshot['people'] = self.people
        snapshot['site_name'] = self.site
        snapshot['description'] = self.description
        snapshot['title'] = self.title
        snapshot['timestamp'] = self.timestamp.compact()
        #root can sometimes be full path to a specific drive
        #here we use it as a relative path, so it's the same as base
        snapshot['content_root'] = self.root
        snapshot['content_base'] = self.root
        snapshot['complete'] = self.complete
        snapshot['media'] = self.media
        return snapshot

    def save(self, destination=None):
        if not destination:
            if self.source:
                destination = self.source
            else:
                raise ValueError, "unknown destination: %s and unknown source: %s" % (destination, self.source)

        d = self.to_dict()

        save_json(destination, d)


    def find_media(self, location, search_for, ignores=[], debug=False):
        """
        search for should be a regular expression, like:
        '.*mp4$'

        ignores is a list of regular expressions to exclude
        """
        media_check = re.compile(search_for)
        alternate = re.compile('.*\.wmv')
        options = []
        alts = []
        if self.root:
            path = os.path.join(location, self.root)
            if os.path.isdir(path):
                for root,dirs,files in os.walk(path):
                    for f in files:
                        ignore = False
                        for i in ignores:
                            if re.search(i, f):
                                ignore = True
                        if not ignore:
                            media = os.path.join(root, f)
                            if media_check.search(f):
                                options.append(media)
                            if alternate.search(f):
                                alts.append(media)

# original version stopped here:
##         if not len(options) and len(alts):
##             return alts
##         else:
##             return options

        if not len(options) and len(alts):
            checking = alts
        else:
            checking = options

        if debug:
            print "before looking at cache, found: %s items" % len(checking)

        matches = []
        for item in checking[:]:
            for m in self.media:
                if item == m[0]:
                    matches.append(m)
                    checking.remove(item)

        if debug:
            print "after looking at cache, matched: %s items" % len(matches)
            print "still need to find: %s new items" % len(checking)

        for item in checking:
            size = get_media_dimensions(item)
            matches.append( [item, size] )

        self.media = matches

        return self.media
            


        
class Collection(list):
    """
    object to hold the complete meta data for a collection of content...
    there are many different ways a collection of content can be represented
      - dictionary based on a common key
      - groups (list of lists)
      - flat list

    generally a flat list is easiest... allows ordering

    When it comes to all of the data stored for a Collection,
    including the Content items, there are different ways to represent them.
    
    Collections are typically local mirrors of remote content
    In some media applications, these could be considered a Subscription
    to an RSS feed.
    As such, they often need to be checked for new content, but the way
    this is done is often customized for the source.
    e.g. not everything *is* RSS based, so a custom scraper is required

    Adding in tailored Content acuisition routines to the Collection would
    cause clutter.

    Subclassing doesn't make much sense either in this case.

    What would probably work best is a plugin customized for the particular
    Collection.

    Looking at YAPSY for this.
    
    """
    def __init__(self, source='', root='', contents=[], walk=False, as_dict=False):
        """
        walk will force a walk, regardless of if a source is available
        """
        #this is a json representation of the whole Collection:
        self.source = source

        #can be useful to look back at how the object was loaded.
        self.walk = walk
        
        #if we were passed a list of contents, apply them
        if len(contents):
            for s in contents:
                if not s in self:
                    self.append(s)

        if source:
            self.root = os.path.dirname(source)
        else:
            self.root = root

        if not root:
            #print "Warning, no root"
            self.summary = None
        else:
            #load CollectionSummary:
            #cs = self.load_collection_summary()
            self.summary = CollectionSummary(self.root)

            self.summary.load_scraper()
            #print "Finished loading scraper: %s" % self.summary.scraper
            #print type(self.summary.scraper)
            #print dir(self.summary.scraper)
            
            #this also makes scraper available via:
            #self.summary.scraper

        if self.root and not self.source:
            meta = self.summary.latest_meta()
            if meta:
                self.source = meta
            else:
                # couldn't find anything, so better walk
                self.walk = True
            
            #if we get this far, contents.json seems like a safer default
            #self.source = os.path.join(self.root, 'contents.json')

        if self.walk:
            #need to know where to walk
            assert root, "NO ROOT SPECIFIED!"
            self.rescan()
        else:
            self.load()
        
    def load(self, source=None):
        if source:
            self.source = source
            
        # do the loading now:
        if self.source:
            if os.path.exists(self.source):
                json_contents = load_json(self.source)
                #this will depend on how json_contents was stored (list vs dict):
                #for content in json_contents.values():

                #if as_dict:
                if isinstance(json_contents, dict):
                    for content in json_contents.values():
                        s = Content(content=content)
                        self.append(s)
                else:
                    # storing as a list seems most versatile
                    # can create a dictionary version later
                    # (too many ways to index)
                    for content in json_contents:
                        #print content
                        s = Content(content=content)
                        self.append(s)
            else:
                print "WARNING: couldn't find contents json path: %s" % self.source
        else:
            raise ValueError, "No source file specified: %s" % self.source

    def save(self, destination=None):
        if not destination:
            #maybe destination should default to source???
            destination = os.path.join(self.root, "contents-saved.json")

        all_contents = []
        for content in self:
            d = content.to_dict()
            all_contents.append(d)

        save_json(destination, all_contents)

    def rescan(self):
        """
        look for all json files that describe the content items
        these should have been generated externally (e.g. during scrape)
        
        json files should contain the main attributes that a Content object has
        the rest will be kept in a remainder

        parsing html and generating json summaries of content
        is beyond the scope of this application
        and should be kept outside of this code base (too specific to content)
        """
        
        #clear out anything else
        del self[:]

        print "walking directory for contents: %s" % self.root
        json_check = re.compile('.*\.json$')
        #it might be inefficient to try to filter these here...
        #too many different names that might work in different contexts
        #ignores = ["contents", "collection", "incompletes"]

        #instead of looking for ignores
        #will limit by convention
        #top level directory should only contain meta jsons
        #(that should be ignored as content data)
        #content jsons will always be in a subdirectory
        #similarly, meta jsons should never be in a subdirectory
        self_root_path = Path(self.root)
        parent = self_root_path.parent()
        if os.path.isdir(self.root):
            #for root,dirs,files in os.walk(self.root):
            subdirs = self_root_path.load().directories
            for subdir in subdirs:
                for root,dirs,files in os.walk(str(subdir)):
                    for f in files:
                        #if json_check.search(f) and not check_ignore(f, ignores):
                        if json_check.search(f):
                            json_file = os.path.join(root, f)
                            p_root = Path(root)
                            relative_root = p_root.to_relative(str(parent))
                            #get rid of leading slash
                            relative_root = relative_root[1:]
                            print "loading content from: %s" % json_file
                            s = Content(json_file, root=relative_root)
                            self.append(s)

        print "Finished loading %s contents manually" % (len(self))

    def reparse(self):
        """
        similar to rescan
        but this time go through and regenerate the individual json files
        for each content item
        from the original HTML source file

        this will utilize the customized Scraper IPlugin module
        for the given Collection

        typically this should be performed by the Scraper itself
        during content scans

        not sure how useful this will be
        other than to make sure integration of YAPSY is working
        """
        ## print "loading logging"
        ## import logging
        ## logging.basicConfig(level=logging.DEBUG)

        logging.debug("walking directory for reparse: %s" % self.root)
        html_check = re.compile('.*\.html$')
        #any directories that do not contain content should be listed here
        ignores = [ "pages", "archive" ]
        self_root_path = Path(self.root)
        parent = self_root_path.parent()

        #probably safe to assume this, but...
        if os.path.isdir(self.root):
            subdirs = self_root_path.load().directories
            for subdir in subdirs:
                if not check_ignore(str(subdir), ignores):
                    for root,dirs,files in os.walk(str(subdir)):
                        for f in files:
                            if html_check.search(f):
                                html_file = os.path.join(root, f)
                                print
                                print
                                print "Starting check of: %s" % html_file

                                json = self.summary.scraper.parse_details(html_file)
                                self.summary.scraper.save_details(json, html_source=html_file)

                                #TODO:
                                #consider moving json saving into parse_details
                                #to avoid duplication of efforts
                                ## p_root = Path(html_file)
                                ## relative_root = p_root.to_relative(str(parent))
                                ## logging.debug("html relative path: %s" % relative_root)
                                ## #get rid of leading slash
                                ## relative_root = relative_root[1:]
                                ## json['root'] = relative_root
                                
                                ## if json.has_key('date'):
                                ##     ts = Timestamp(json['date'])
                                ## else:
                                ##     ts = Timestamp(f.split('.')[0])
                                ##     json['date'] = str(ts.compact(accuracy="day"))
                                ## json_path = os.path.join(root, ts.filename(".json"))
                                
                                ## save_json(json_path, json)

                                ## self.append(s)
                                #(or rescan)

        print "Finished parsing %s contents manually" % (len(self))
        self.rescan()



    def update(self, new_group):
        """
        clear out everything we hold
        then apply everything in the new_group

        this preserves all attributes for the Collection object (meta data)
        (rather than instantiating a new version)

        also [2012.09.21 12:40:12]
        this can be done more suscinctly with
        del self[:]
        self.extend(new_group)
        
        """
        print "clearing contents: %s" % len(self)

        for item in self[:]:
            self.remove(item)

        print "should be clear (0): %s" % len(self)

        for item in new_group:
            self.append(item)
            
        print "applied new order: %s" % len(self)
        
    def sort_by_date(self, debug=False):
        dates = []
        for i in self:
            dates.append( [i.timestamp.compact(), i] )

        new_order = []
        dates.sort()
        dates.reverse()
        for d in dates:
            if debug:
                print d[0]
            new_order.append(d[1])

        self.update(new_order)

    def load_cluster(self, cluster_file=None):
        """
        if no cluster_file is specified explicitly
        look through all available cluster files
        and choose the right one based on most recent date
        """
        pass




class CollectionSummary(object):
    """
    summary of a drive or a collection

    includes:
     - directories with collection data / images
     - json item lists
     - collection indexes

     this might be a good place to make parent class for subclassing for
     plugins based on YAPSY and IPlugins.
    """
    def __init__(self, root):
        #if this changes, might need to rename existing files to stay consistent
        #aka: index.json, collection-meta.json
        self.file = 'summary.json'

        self.root = root
        self.name = os.path.basename(root)
        if not self.name:
            #maybe there was a trailing slash... this should fix that:
            self.name = os.path.basename(os.path.dirname(root))

        #other places to find media for this collection
        #aka: 'drives'
        self.locations = []
        self.available = []

        # a place to keep track of the local json meta indexes
        # and the last time that this system accessed that index
        self.metas = {}

        #do not store with collection (might take too long to load quickly)
        #self.items = []

        #data loaded from json representation
        self.json_data = {}

        #not loaded by default
        self.collection = None

        self.load()
        self.scan_metas()

        for l in self.locations:
            if os.path.exists(l):
                self.available.append(l)
        

        self.save()


    def __str__(self):
        return self.name

    def summary(self):
        print "Name: %s" % (self.name)
        print "Root: %s" % (self.root)
        print "Locations: %s" % (self.locations)
        print "Available: %s" % (self.available)
        print "JSON Meta Files: %s" % (self.metas)
        print ""

    def load(self, json_file=None):
        """
        load previously stored meta data
        """
        if not json_file:
            json_file = os.path.join(self.root, self.file)

        if not os.path.exists(json_file):
            print "WARNING: couldn't find json on collection load: %s" % (json_file)
        else:
            self.json_data = load_json(json_file)
            if self.json_data.has_key('locations'):
                self.locations = self.json_data['locations']
            if self.json_data.has_key('metas'):
                self.metas = self.json_data['metas']        

    def save(self, json_file=None):
        """
        save current data for faster lookup next time
        """
        if not json_file:
            json_file = os.path.join(self.root, self.file)

        #collection = { 'locations':self.locations, 'metas':self.metas }
        self.json_data['locations'] = self.locations
        self.json_data['metas'] = self.metas
        self.json_data['name'] = self.name
        self.json_data['root'] = self.root
        save_json(json_file, self.json_data) 

    def load_scraper(self):

        #print "loading logging"
        #import logging
        #logging.basicConfig(level=logging.DEBUG)
        
        print "loading scraper from: %s" % self.root
        # Build the manager
        simplePluginManager = PluginManager(plugin_info_ext="medley-plugin")
        # Tell it the default place(s) where to find plugins
        #simplePluginManager.setPluginPlaces(["path/to/myplugins"])
        simplePluginManager.setPluginPlaces([self.root])
        # Load all plugins
        simplePluginManager.collectPlugins()    

        number_found = len(simplePluginManager.getAllPlugins())
        print "Activate all loaded plugins: %s" % number_found
        for plugin in simplePluginManager.getAllPlugins():
            #plugin.plugin_object.print_name()
            
            print "Activating: %s" % plugin.name
            simplePluginManager.activatePluginByName(plugin.name)

        #self.scraper = simplePluginManager.getPluginByName(plugin.name)
        self.scraper = simplePluginManager.getPluginByName(self.name).plugin_object
        

    def load_collection(self, json_file=None):
        """
        load the corresponding collection object
        should automatically determine the latest version of the meta file
        and default to that if no other json_file is specified manually

        and if none, exists, walk should be called automatically
        """
        collection = None
        if json_file is None:
            meta = self.latest_meta()
            if meta:
                collection = Collection(meta)
            else:
                collection = Collection(root=self.root, walk=True)
        else:
            collection = Collection(json_file)

        #keep track of it here, once it has been loaded
        self.collection = collection

        return collection


    def latest_meta(self):
        """
        look through all metas, and return the newest one
        """
        if not len(self.metas.items()):
            self.scan_metas()
            #if still no metas exists, then nothing to return
            if not len(self.metas.items()):
                return None


        assert len(self.metas.items())
        #find newest meta now
        for name in self.metas.keys():
            #http://stackoverflow.com/questions/1059559/python-strings-split-with-multiple-separators
            parts = re.findall(r'\w+', name)
            print parts
            #TODO: identify datestring, choose based on datestring
        

    def scan_metas(self):
        """
        go through our list of JSON meta files
        make sure any previously found ones still exist
        add new ones        
        """
        options = os.listdir(self.root)
        if self.file in options:
            self.load()
            options.remove(self.file)

        old_metas = self.metas.keys()
            
        for o in options:
            if re.search('.*\.json$', o):
                if not self.metas.has_key(o):
                    #self.metas.append(o)
                    self.metas[o] = { 'length':None, 'updated':None }

                if o in old_metas:
                    old_metas.remove(o)

        # clean up any old items
        for o in old_metas:
            del self.metas[o]

class Collections(list):
    """
    object to hold multiple CollectionSummary objects
    with methods to help loading and lookups
    """
    def __init__(self, root, collection_list=[]):
        self.root = root

        #keep track if we've already called load:
        self.loaded = False
        
        # should be a list of paths only
        # if a path is relative (starts with './') use self.root
        # otherwise assume it is a full path
        self.paths = collection_list
        if collection_list:
            self.load_summaries(collection_list)

        # we will store actual CollectionSummary objects in self

    def scan(self, debug=False):
        """
        return a list of path options local to self.root

        this does *NOT* update self.paths...
        that is left up to the caller if it is appropriate
        """
        names = os.listdir(self.root)
        options = []
        for name in names:
            #options.append( (name, os.path.join(self.root, name)) )
            options.append( os.path.join(self.root, name) )

        paths = []
        for o in options:
            if os.path.isdir(o):
                paths.append(o)

        return paths

    def add(self, path):
        """
        add a path to the collection.paths
        then load the one path

        used for loading externally
        """
        if not path in self.paths:
            if os.path.isdir(path):
                self.paths.append(path)
                c = CollectionSummary(path)
                self.append(c)
            else:
                raise ValueError, "Non-directory item sent to add: %s" % path
        else:
            print "Path: %s already in collections.paths" % path
    
    def load_summaries(self, collection_list=[]):
        """
        (re)load any collections

        will over-write self.paths with collection_list if passed in
        """
        #clear out our contents first
        del self[:]
        
        if collection_list:
            self.paths = collection_list
            
        for path in self.paths:
            if re.match('^\.', path):
                path = os.path.join(self.root, path[2:])
            if os.path.isdir(path):
                c = CollectionSummary(path)
                self.append(c)
            else:
                raise ValueError, "Non-directory item in Collections.paths: %s" % path

        self.loaded = True

    def get_summary(self, name, debug=False):
        """
        return the first collection with a name that matches 'name'
        """
        if debug:
            print "Getting collection: %s from: %s" % (name, self.root)

        if not self.loaded:
            self.load_summaries()
            
        for collection_summary in self:
            if collection_summary.name == name:
                if debug:
                    print "%s  matches: %s" % (name, collection_summary.name)
                return collection_summary
            else:
                if debug:
                    print "%s doesn't match: %s" % (name, collection_summary.name)
        return None

    def setup(self):
        """
        set up new structure based on initialized root

        will probably do this elsewhere, but just in case...
        """
        if not os.path.exists(self.root):
            os.makedirs(self.root)

        for path in self.paths:
            if re.match('^\.', path):
                path = os.path.join(self.root, path[2:])
            # if path is a full path already, and not under self.root
            # it may already exist
            if not os.path.exists(path):
                os.makedirs(path)

class Cluster(list):
    """
    A Cluster is essentially a list of clouds.
    These are useful for grouping like items with like items.


    clusters were once referred to as groups
    but that is too generic of a name in this case
    these are really clusters of clouds

    these clusters can be applied to media lists (Items)
    to generate intricate playlists based on a number of factors
    """

    def __init__(self, source=None, ordered_list=[ [], [], [], [], [], [], [], [], [], [], ]):
        self.extend(ordered_list)
        self.source = source
        
    #def save_groups(self, destination, ordered_list):
    def save(self, destination=None):
        """
        similar to save json, but custom formatting to make editing easier

        to load, use collection.load_groups

        """
        if destination is None:
            destination = self.source

        if not destination:
            raise ValueError, "No destination specified: %s" % destination
        
        json_file = codecs.open(destination, 'w', encoding='utf-8', errors='ignore')
        #split = json.dumps(ordered_list)
        split = json.dumps(self)
        split = split.replace('], ', ', ], \n')
        split = split.replace(']]', ', ]]')
        json_file.write(split)
        json_file.close()    

    #def load_groups(self, source):
    def load(self, source=None, create=False):
        """
        """
        if source is None:
            source = self.source

        if not source:
            raise ValueError, "No source specified: %s" % source
                
        if not os.path.exists(source):
            if create:
                self.save(source)
            else:
                raise ValueError, "Source file does not exist: %s" % source


        groups = []
        json_file = codecs.open(source, 'r', encoding='utf-8', errors='ignore')
        lines = json_file.readlines()
        #unsplit the items and put them back into a standard json format
        unsplit = ''
        for line in lines:
            if not re.match("#", line):
                line = line.replace(',]', ']')
                line = line.replace(', ]', ']')
                unsplit += line.strip() + ' '

        try:
            groups = json.loads(unsplit)
        except:
            #try to pinpoint where the error is occurring:
            #print unsplit

            #get rid of outer list:
            unsplit = unsplit[1:-1]
            parts = unsplit.split('], ')
            #assert len(parts) == 11
            count = 0
            for p in parts:
                p = p + ']'
                try:
                    group = json.loads(p)
                except:
                    new_p = p[1:-1]
                    tags = new_p.split('", "')
                    summary = ''
                    for tag in tags:
                        summary += tag + "\n"

                    #print count
                    #print summary
                    print "%s - %s" % (count, summary)
                    raise ValueError, "Trouble loading JSON in part %s: %s" % (count, summary)
                count += 1

        json_file.close()

        del self[:]
        self.extend(groups)

        return groups
    
