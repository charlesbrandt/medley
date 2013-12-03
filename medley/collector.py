"""
Main objects needed for sorting collections.

Collection and Content may need to be customized for the specific type of colleciton in use. 

OVERVIEW:
============

A Collections object is created with the root location and the list of acceptable collection directories available.  These option are generally stored as a JSON file named 'config.json' in the root of the collections directory, but could easily be generated and passed in at run time. The main function is to load and store all of the CollectionSummary objects.

A CollectionSummary will look for a 'summary.json' file in either the main root directory associated with the CollectionSummary, or in the meta subdirectory of the main root directory (meta_root).  This summary data includes other drive locations where the Collection and all other associated data may be found.

"""
import os, re, logging, codecs

#used in Cluster.save():
import json

from helpers import load_json, save_json

from content import Content

from moments.path import Path, check_ignore
from moments.timestamp import Timestamp
from moments.journal import Journal

from medley.yapsy.PluginManager import PluginManager

class CollectionSimple(list):
    """
    Collection is getting a bit too smart
    which makes it complicated...
    generally just want a source (and root) so we know where things come from
    Content is much more important
    """
    def __init__(self, source='', root='', contents=[], walk=False, as_dict=False, debug=False):
        """
        source should be the full path to source        
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

        ## if not root:
        ##     #print "Warning, no root"
        ##     self.summary = None

    def save(self, destination=None):
        if not destination:
            #maybe destination should default to source???
            destination = os.path.join(self.root, "contents-saved.json")

        all_contents = []
        for content in self:
            d = content.to_dict()
            all_contents.append(d)

        save_json(destination, all_contents)

    #aka walk()
    def rescan(self, ignores=[], debug=False):
        """
        look for all json files that describe the content items
        these should have been generated externally (e.g. during scrape)
        
        json files should contain the main attributes that a Content object has
        the rest will be kept in a remainder

        parsing html and generating json summaries of content
        is beyond the scope of this application
        and should be kept outside of this code base (too specific to content)
        """

        if not self.root:
            raise ValueError, "Cannot rescan. No root set on collection: %s" % self.root
        
        #clear out anything else
        del self[:]

        if debug:
            print "walking directory for contents: %s" % self.root

        json_check = re.compile('.*\.json$')

        #it might be inefficient to try to define these here...
        #too many different names that might work in different contexts
        #ignores = ["contents", "collection", "incompletes"]
        #can pass them in if needed...
        
        self_root_path = Path(self.root)
        parent = self_root_path.parent()
        if not os.path.isdir(self.root):
            self.root = os.path.dirname(self.root)
            #if we still don't have a directory, something is wrong with root
            assert os.path.isdir(self.root)

        
        #instead of looking for ignores
        #will limit by convention
        #top level directory should only contain meta jsons
        #(that should be ignored as content data)
        #content jsons will always be in a subdirectory
        #similarly, meta jsons should never be in a subdirectory

        #for root,dirs,files in os.walk(self.root):
        subdirs = self_root_path.load().directories
        for subdir in subdirs:
            for root,dirs,files in os.walk(str(subdir)):
                for f in files:

                    #if json_check.search(f):
                    if json_check.search(f) and not check_ignore(f, ignores):
                        json_file = os.path.join(root, f)
                        p_root = Path(root)
                        relative_root = p_root.to_relative(str(parent))
                        #get rid of leading slash
                        if re.match('/', relative_root):
                            relative_root = relative_root[1:]
                        if debug:
                            print "loading content from: %s" % json_file
                        #c = Content(json_file, root=relative_root)
                        c = Content(json_file)
                        if debug:
                            print "setting base_dir to: %s" % relative_root
                        c.base_dir = relative_root
                        self.append(c)

        if debug:
            print "Finished loading %s contents manually" % (len(self))


class Collection(CollectionSimple):
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

    Adding in tailored Content acquisition routines to the Collection would
    cause clutter.

    Subclassing doesn't make much sense either in this case. (???)

    What would probably work best is a plugin customized for the particular
    Collection.

    Looking at YAPSY for this.
    
    """
    def __init__(self, source='', root='', contents=[], walk=False, as_dict=False, debug=False):
        """
        source should be the full path to source
        
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

            #do we always need this???
            print "LOADING COLLECTION SUMMARY AT: %s" % self.root
            self.summary = CollectionSummary(self.root)
            #pass
        
            #TODO:
            #*2012.11.09 12:15:37 
            #this should be optional or configurable
            #can take a while to scan for a meta directory 
            #with a lot of meta data
            #self.summary.load_scraper()

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
            assert self.root, "NO ROOT SPECIFIED!"
            self.rescan()
        elif self.source:
            if debug:
                print "Loading Collection from: %s" % self.source
            self.load(debug=debug)
        else:
            #might want to create one from scratch.
            pass
        
        #whether or not to update a content's source json file
        #or just make the changes to the list locally
        #
        #generally with a playlist you don't want to update the content source
        #e.g. subtractively limiting content segments to only favorites...
        #     wouldn't want to remove those segments from the content source
        #     just from the current playlist
        #
        #this should not matter if a content object is edited directly
        self.sync_contents = True

    def load(self, source=None, debug=False):
        """
        load a collection from a previously generated summary json file
        should contain all data for all included content items
        this content would have been assembled in a previous scan
        """
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
                    if debug:
                        print "Reading JSON as dictionary"
                    for content in json_contents.values():
                        s = Content(content=content)
                        s.load()
                        if debug:
                            print s
                        self.append(s)
                else:
                    if debug:
                        print "Reading JSON as list"
                    # storing as a list seems most versatile
                    # can create a dictionary version later
                    # (too many ways to index)
                    for content in json_contents:
                        if debug:
                            print content
                        s = Content(content=content)
                        s.load()
                        self.append(s)
            else:
                print "WARNING: couldn't find contents json path: %s" % self.source
        else:
            raise ValueError, "No source file specified: %s" % self.source


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
        print "MAY WANT TO CALL LOAD CLUSTER DIRECT ON SUMMARY!"
        return self.summary.load_cluster()




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
        #just incase meta files are not stored in the root of the collection
        self.meta_root = root
        
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
        self.scraper = None
        self.cluster = None

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
            #check one more place...
            #common to keep these files in a 'meta' directory
            alt_json_file = os.path.join(self.root, 'meta', self.file)
            json_file = alt_json_file
            self.meta_root = os.path.join(self.root, 'meta')
            if not os.path.exists(alt_json_file):
                print "WARNING: couldn't find json on collection load: %s" % (json_file)
                                

        #now see if we have something
        if os.path.exists(json_file):
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
            json_file = os.path.join(self.meta_root, self.file)

        #collection = { 'locations':self.locations, 'metas':self.metas }
        self.json_data['locations'] = self.locations
        self.json_data['metas'] = self.metas
        self.json_data['name'] = self.name
        self.json_data['root'] = self.root
        self.json_data['meta_root'] = self.meta_root
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
        plugin = simplePluginManager.getPluginByName(self.name)
        if plugin:
            self.scraper = plugin.plugin_object
        else:
            self.scraper = None
        

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
            print "self.latest_meta() results: %s" % meta
            if self.meta_root:
                #Collection will set root accordingly if meta has full path
                meta = os.path.join(self.meta_root, meta)
                print "after join: %s" % meta
                collection = Collection(meta)
            else:
                collection = Collection(root=self.root, walk=True)
        else:
            collection = Collection(json_file)

        #keep track of it here, once it has been loaded
        self.collection = collection

        return collection

    def load_cluster(self, json_file=None):
        """
        load the corresponding cluster object
        should automatically determine the latest version of the meta file
        and default to that if no other json_file is specified manually

        """
        print "LOADING CLUSTER: "
        cluster = None
        if json_file is None:
            meta = self.latest_groups()
            print "meta: %s (None means no clusters/.groups files found)" % meta
            if meta:
                meta = os.path.join(self.meta_root, meta)
                cluster = Cluster(meta)
            else:
                #TODO:
                #could generate an intial list of all group items
                #available in the collection
                #this may be collection specific though
                cluster = Cluster()

        else:
            cluster = Cluster(json_file)

        #keep track of it here, once it has been loaded
        self.cluster = cluster

        return cluster

    #aka def latest_cluster(self):
    def latest_groups(self, debug=True):
        """
        similar to latest_meta
        but only returns the groups/cluster meta
        """
        if not len(self.metas.items()):
            self.scan_metas()
            #if still no metas exists, then nothing to return
            if not len(self.metas.items()):
                print "No meta found in scan (latest_groups())"
                return None


        assert len(self.metas.items())

        metas = []
        groups = []
        for name in self.metas.keys():
            if re.search('.*\.groups', name):
                groups.append(name)
            else:
                metas.append(name)


        print "FOUND THE FOLLOWING GROUP OPTIONS (%s): %s" % (len(groups), groups)
        newest_group = None
        newest_date = None
        #find newest group now
        for name in groups:
            #http://stackoverflow.com/questions/1059559/python-strings-split-with-multiple-separators
            #w+ = a word character (a-z etc.) repeated one or more times
            #match all of those regardless of separator
            parts = re.findall(r'\w+', name)
            #print parts
            for part in parts:
                try: 
                    ts = Timestamp(part)
                    #print ts
                    if newest_date and (ts.datetime > newest_date.datetime):
                        #print "Found a newer group: %s (previously: %s)" % (
                        #    name, newest_date.compact())
                        newest_date = ts
                        newest_group = name
                    elif not newest_date:
                        newest_date = ts
                        newest_group = name
                    else:
                        #must be an older item 
                        pass
                    
                except:
                    #must not be a datestring
                    pass
                
        return newest_group


    def latest_meta(self):
        """
        look through all metas, and return the newest one

        two meta items in common use,
        the full collection representation

        and the grouping of various meta data into "groups" files
        """
        if not len(self.metas.items()):
            self.scan_metas()
            #if still no metas exists, then nothing to return
            if not len(self.metas.items()):
                print "No meta found in scan"
                return None


        assert len(self.metas.items())

        metas = []
        groups = []
        for name in self.metas.keys():
            if re.search('.*\.groups', name):
                groups.append(name)
            else:
                metas.append(name)
            
        newest_meta = None
        newest_date = None
        #find newest meta now
        for name in metas:
            #http://stackoverflow.com/questions/1059559/python-strings-split-with-multiple-separators
            #w+ = a word character (a-z etc.) repeated one or more times
            #match all of those regardless of separator
            parts = re.findall(r'\w+', name)
            #print parts
            for part in parts:
                try: 
                    ts = Timestamp(part)
                    #print ts
                    if newest_date and (ts.datetime > newest_date.datetime):
                        #print "Found a newer meta: %s (previously: %s)" % (
                        #    name, newest_date.compact())
                        newest_date = ts
                        newest_meta = name
                    elif not newest_date:
                        newest_date = ts
                        newest_meta = name
                    else:
                        #must be an older item 
                        pass
                    
                except:
                    #must not be a datestring
                    pass
                
        return newest_meta

    def scan_metas(self):
        """
        go through our list of JSON meta files
        make sure any previously found ones still exist
        add new ones        
        """
        if not os.path.exists(self.meta_root):
            os.makedirs(self.meta_root)

        options = os.listdir(self.meta_root)
        print "scan_metas in %s, %s options found" % (self.meta_root, len(options))
        if self.file in options:
            #self.load()
            options.remove(self.file)

        old_metas = self.metas.keys()

        ignores = [ '~', ]

        #*2012.11.09 11:47:34
        #not always ending in .json anymore
        #(but should always have .json in the name)            
        for o in options:
            if re.search('.*\.json', o) and not check_ignore(o, ignores):
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
            print "Updating Collections.paths to: %s" % collection_list
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

    def __init__(self, source=None, ordered_list=[]):
        self.extend(ordered_list)
        self.source = source
        if self.source:
            self.load()

        #used in from_cloud and to_cloud
        self.tag = None
        
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
            print unsplit

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
                    #print "%s - %s" % (count, summary)
                    raise ValueError, "Trouble loading JSON in part %s: %s" % (count, summary)
                count += 1

        json_file.close()

        del self[:]
        self.extend(groups)

        return groups
    

    def from_cloud(self, cloud_file, tag):
        """
        sometimes clusters are stored in a cloud file
        less decoration in that case

        tag will be used to find the latest entry with that tag
        
        """
        self.source = cloud_file
        self.tag = tag
        clouds = Journal(cloud_file)

        if clouds.tag(tag):
            lines = clouds.tags(tag)[0].data.splitlines()
        else:
            print "no ->%s<- tags found!" % tag

        #print len(lines)
        groups = []
        for l in lines:
            new_group = l.split()
            groups.append(new_group)
        
        del self[:]
        self.extend(groups)

        return groups

    def to_cloud(self, destination=None, tag=None):
        if destination is None:
            print "Using previous source: %s" % self.source
            destination = self.source
            #print "Using previous source: %s" % ('temp.txt')
            #destination = 'temp.txt'
        if tag is None:
            tag = self.tag

        if not tag:
            raise ValueError, "Need a tag! (%s)" % tag
        
        data = ''
        ct = 0
        for group in self:
            #if you want numbers in the group:
            #for i in range(20):
            #    if str(i) in g:
            #        g.remove(str(i))
            #group.insert(0, str(ct))
            
            data += " ".join(group) + '\n'
            ct += 1

        clouds = Journal(destination)
        #make_entry
        clouds.make(data=data, tags=[tag])
        clouds.save(destination)
        print "Saved cloud: %s" % destination
        
    
    def remove(self, ignores):
        """
        go through lists and remove all matching items in ignores
        """

        count = 0
        for group in self:
            for item in group:
                if item in ignores:
                    print "removing item: %s" % item
                    group.remove(item)
                    count += 1
        print "Removed: %s items from: %s" % (count, self.source)
        print

    def flatten(self, remove_dupes=True):
        flat = []
        for group in self:
            #print len(group)
            for item in group:
                if (not item in flat):
                    flat.append(item)
                else:
                    if remove_dupes:
                        print "removing dupe: %s" % item
                        group.remove(item)
                    else:
                        print "keeping dupe: %s" % item
                        
            #print len(group)

        return flat

    def position(self, lookup):
        """
        similar to contains, but returns the exact position if it exists
        """
        match = None
        group_num = 0
        for group in self:
            #print len(group)
            if lookup in group:
                match = (group_num, group.index(lookup))

            group_num += 1
        return match

    def contains(self, lookup):
        """
        helper
        just flattens all lists and sees if lookup is in that
        """
        flat = self.flatten()
        if lookup in flat:
            return True
        else:
            return False

    def add_at(self, item, position):
        """
        take the item and add it to the sub group at position
        if position is out of range for the cluster's length
        add extra lists to pad it out
        """
        while position >= len(self):
            self.append([])

        #remove from anywhere else first:
        self.remove( [item] )
        self[position].append(item)
        
    def merge_in(self, incoming, add_new=False, keep_order=False):
        """
        take the incoming cluser and merge its items in, moving our items around
        incoming will be taken as the authority on group membership

        incoming should be modified before merge in
        if anything should not be merged

        e.g. current unsorted items...
        wouldn't want those to undo items sorted elsewhere

        if you want to add new items, be sure to set add_new to True

        keep_order will keep the existing order of items in this group
        probably not what you want
        """

        self_all = self.flatten()
        incoming_all = incoming.flatten()

        #expand self to be legth of incoming:
        if len(incoming) > len(self):
            size_diff = len(incoming) - len(self)
            print "EXPANDING CLUSTER BY %s" % size_diff
            for ct in range(size_diff):
                self.append([])

        for ct in range(len(self)):
            if len(incoming) <= ct:
                print "skipping index: %s (incoming too short: %s)" % (ct, len(incoming))
            else:
                print "checking index: %s" % (ct)
                cur_self = self[ct]
                cur_incoming = incoming[ct]

                print "%s items in self.  %s items in incoming" % (len(cur_self), len(cur_incoming))

                new_ct = 0

                #place to keep track of the new order being applied by incoming
                new_sub = []
                
                for item in cur_incoming:
                    if (not item in self_all) and add_new:
                        if keep_order:
                            cur_self.append(item)
                        else:
                            new_sub.append(item)
                        print "New item added: %s" % item
                    elif not item in self_all:
                        print "Skipping new item: %s" % item
                        print
                    elif not item in cur_self:
                        #need to go find it in another group and remove it
                        for sub_ct in range(len(self)):
                            if sub_ct != ct and (item in self[sub_ct]):
                                self[sub_ct].remove(item)
                                if keep_order:
                                    cur_self.append(item)
                                else:
                                    new_sub.append(item)
                                    
                                if sub_ct < ct:
                                    print "down: %s (from %s to %s)" % (item, sub_ct, ct)
                                else:
                                    print "up:   %s (from %s to %s)" % (item, sub_ct, ct)

                    else:
                        #must be in the current group...
                        #just need to check order preferences
                        if not keep_order:
                            new_sub.append(item)
                            cur_self.remove(item)

                if not keep_order:
                    new_sub.extend(cur_self)
                    self[ct] = new_sub

                print "%s: now %s items in destination (self)" % (ct, len(cur_self))
                print
