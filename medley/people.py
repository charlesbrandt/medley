"""
*2013.11.12 11:11:56
A place to define a person related to a piece of content.

Could think of this as the ForeignKey referenced by the Content.people list

Should not store large content here... that should be kept with the collection.
Should store an index with references to collections.
Could store small meta data like cover art, as a reference / reminder

might be good to have some qualities of Content referenced locally

see also people_create.py 
"""
import os, re, copy, json

from collector import Cluster, CollectionSimple
from helpers import save_json, load_json
from moments.tag import to_tag

class ContentPointer(object):
    """
    Refer to a specific Content object
    only hold the items necessary to Summarize/describe it locally
    similar to what is done in playlists that refer to Content
    should be easy to put the gist of this on a playlist
    """
    def __init__(self):
        #where the full json source originates
        self.original_path = ''        
        self.collection_name = ''

        #may not always be up to date if parent directory changes
        self.original_full_path = ''

        #for estimating size later (even if it might not be available)
        self.size = ''



class Person(object):
    def __init__(self, source='', tag='', debug=False):
        """
        set up the basics
        """
        #for disply purposes only
        self.name = ''

        self.debug = debug
        
        if tag:
            #aka main tag
            self.tag = tag        
            #keep track of all alternative spellings here
            self.tags = [ tag ]
        else:
            self.tag = ''
            self.tags = []

        self.local_path = ''

        #these should be read only (don't want to have to synchronize changes)
        #don't make changes to the json files they were loaded from either!
        self.contents = []

        #ok to store this list
        #just a list of base_dirs for each content item
        self.content_order = []

        #keep track of the last length of contents after a load_content call
        self.count = ''

        #cutoffs is a list of numbers
        #each number specifies a position in the contents
        #where a different class of content starts
        #cutoff tags gives a label to each of those cutoffs
        #
        #stored as a comma separated string for easier editing
        #can split when using in scripts
        self.cutoffs = ''
        self.cutoff_tags = ''

        #will depend on content type:
        #e.g. sounds like, looks like, etc...
        self.similar_to = ''

        #correspond to main cluster group?
        self.rating = ''
        self.quote = ''
        self.notes = ''

        #verified links only
        self.links = ''

        #path, should be locally available
        self.image = ''

        if source:
            #drive dir
            self.root = source
            self.load()
        else:
            self.root = ''

    def __repr__(self):
        return "Person: %s" % self.tag

    def split_tag(self):
        return self.tag.replace('_', '+')
        
    #TODO:
    #this might be better as a property
    def main_dir(self):
        return os.path.join(self.root, self.tag)        

    def make_path(self, root=None):
        if root:
            self.root = root

        if not self.root:
            raise ValueError, "No root specified: %s" % self.root
        
        main_dir = self.main_dir()
        if not os.path.exists(main_dir):
            os.makedirs(main_dir)

        if not self.tag:
            self.tag = os.path.basename(self.root)
            #could also look for any json file here using medley.helpers
            #but should fail if names are not kept in sync
            
        filename = "%s.json" % self.tag
        main_file = os.path.join(main_dir, filename)
        return main_file

    def as_json(self):
        """
        for using a person object in javascript
        """
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        """
        simplified version of creating a simple dict object
        """
        #print self.__dict__
        #???
        temp_d = copy.copy(self.__dict__)
        #make sure to ignore loaded/scanned contents on a save
        temp_d.pop("contents", None)
        #getting rid of old format... could convert, but nothing has this set:
        temp_d.pop("default_image", None)
        #this is only used locally
        temp_d.pop("debug", None)

        return temp_d

    def save(self, root=None):
        """
        make a directory if none exists
        save the results
        """
        #create an appropriate directory
        #save the person meta data
        if root:
            self.root = root

        if not self.root:
            raise ValueError, "Need a root to know where to save: %s" % self.root
         
        dest_file = self.make_path(self.root)
        #print dest_file
        temp_d = self.to_dict()
        
        #save_json(dest_file, self.__dict__)
        print "Saving: %s to %s" % (temp_d, dest_file)
        save_json(dest_file, temp_d)
        

    def load(self, root=None):
        source_file = self.make_path(root)
        result = load_json(source_file)
        if self.debug:
            print "Loaded: %s" % result
        self.__dict__.update(result)

    #making this a separate call...
    #when loading people, load() is called
    #don't want to scan for content in that case...
    #only when it is requested
    def load_content(self, debug=False):
        md = self.main_dir()

        #scan for local content directories here
        self.contents = CollectionSimple(root=md)
        #ok to use collection for walking here.
        self.contents.rescan(debug=debug)

        #check self.content_order
        #apply order to contents
        #place any new items at the beginning of the list

        #print self.contents

        self.contents.apply_order(self.content_order, debug=debug)

        #update content_order accordingly
        #update order with anything new
        self.content_order = self.contents.get_order()
        if debug:
            print self.content_order

        #update the count:
        self.count = len(self.contents)
        self.save()
        
    def update_default(self, new_tag):
        """
        update our default tag
        rename our directory and main meta file accordingly
        """
        new_dir = os.path.join(self.root, new_tag)
        if os.path.exists(new_dir):
            raise ValueError, "Destination exists: %s (from %s)" % (new_dir, self.tag)

        original_file = self.make_path()
        original_dir = os.path.join(self.root, self.tag)

        new_name = "%s.json" % new_tag
        new_file = os.path.join(original_dir, new_name)
        #rename the file first, to make paths easier
        os.rename(original_file, new_file)
        
        #now move the directory
        os.rename(original_dir, new_dir)

        self.tag = new_tag
        #now save it to our new destination (should over-write old data)
        self.save()

    def update_image(self, drive_dir, force=False, debug=False):
        update = False
        if force:
            update = True
        elif not self.image:
            update = True
        else:
            #must have a default image and not forcing an update... skip
            pass

        if update:
            self.load_content()
            #can only do something if we have some content
            if len(self.contents):
                first = self.contents[0]
                if not first.image or force:
                    #if force set, look again
                    
                    #need to set this to use
                    #the locally cached people directory:
                    first.drive_dir = drive_dir
                    first.find_image(ignores=[], debug=debug)

                if first.image:
                    self.image = first.image
                    if debug:
                        print "updating %s image to %s" % (self.tag, self.image)
                    self.save()
                    
                else:
                    if debug:
                        print "No image associate with first content: %s" % self.tag
                        print "%s contents total" % len(self.contents)
                    
            else:
                if debug:
                    print "No content found for %s" % self.tag
                
        else:
            if debug:
                print "Not updating: %s" % self.tag

class People(list):
    """
    object to load all Person objects into
    to facilitate Person lookup based on tag

    see also: collector.cluster
    similar idea, but rather than holding a list of tag strings
    this holds a list of Person objects.

    also no concept of bins/groups/clusters here... one big list
    use a cluster for sorting

    very similar to a CollectionSummary too
    """
    def __init__(self, source='', term='', debug=False):
        """
        pass in the people term from the config
        """
        if debug:
            print source
        options = os.listdir(source)
        if debug:
            print options
        self.debug = debug

        self.root = source
        if 'meta' in options:
            self.meta_root = os.path.join(self.root, 'meta')
        else:
            #should use meta root, but fail if it doesn't exist
            #or could create it here...
            #concerned that that may cause recursive dirs if meta root passed in
            self.meta_root = None
            raise ValueError, "Could not find meta root in: %s" % source
        
        options = os.listdir(self.meta_root)
        #print options
        #self.cloud_file = os.path.join(self.meta_root, "clouds.txt")

        #moving this to a different file...
        #don't want to log each entry separately
        self.cloud_file = os.path.join(self.meta_root, "people.txt")
        if not os.path.exists(self.cloud_file):
            raise ValueError, "Could not find cloud file: %s" % self.cloud_file

        #this loads the cluster:
        self.cluster = Cluster()
        self.cluster.from_cloud(self.cloud_file, term)

    def load(self, root=None):
        """
        look at all directories and load the corresponding person object
        """
        options = os.listdir(self.root) 
        if 'meta' in options:
            options.remove('meta')

        missing = []
        #print options
        for option in options:
            path = os.path.join(self.root, option)

            #sometimes paths are updated, but content takes time to migrate
            #should catch this and alert someone to update accordingly
            try:
                person = Person(path)
                self.append(person)
            except:
                missing.append(option)
                
        if self.debug:
            print "People loaded: " 
            self.summary()

        if missing:
            for item in missing:
                matches = self.get(item)
                print "MISSING: %s, please move to: %s" % (item, matches[0])

            raise ValueError, "Missing content detected... please fix"
        
    #aka lookup
    def get(self, name):
        """
        go through all People in self and look for any that match
        the tag version of name
        return those results
        (ideally should only be one, but sometimes that might not happen)
        """
        tag = to_tag(name)
        matches = []
        for person in self:
            if tag in person.tags:
                matches.append(person)

        return matches

    def get_first(self, name):
        """
        just return the first item (or None) from a get request
        """
        matches = self.get(name)
        if len(matches):
            first = matches[0]
        else:
            first = None
        return first

    def search(self, name):
        """
        go through all People in self
        look for any with parts that match the different parts of name
        return those results
        """
        #lowest common denominator here:
        tag = to_tag(name)
        parts = tag.split('_')
        
        tallies = []
        for person in self:
            pmatches = 0
            for ptag in person.tags:
                #look at each part of the supplied name/tag
                for part in parts:
                    #make sure we don't have short string...
                    #would match too many tags if so
                    if (len(part) > 2) and re.search(part, ptag):
                        pmatches += 1
            if pmatches:
                tallies.append( (pmatches, person) )

        tallies.sort()
        tallies.reverse()

        #sorting based on number of matches was not as useful as expected
        #usually want the options that start with the same letter
        #updating results to reflect that here:
        matches = []
        same_start = []
        for t in tallies:
            #print tag[0]
            #print t[1]
            if re.match(tag[0], t[1].tag):
                same_start.append(t[1])
            else:
                matches.append(t[1])

        #ok to sort alphabetically here
        matches.sort()
        same_start.extend(matches)
        return same_start

    def summary(self):
        """
        show a simple debug version of self
        """
        opt_count = 0
        for option in self:
            print "%s. %s" % (opt_count, option.tag)
            opt_count += 1
        print ""

    def everyone(self, alts=True):
        """
        return a list of all loaded people tags
        if alts is True, include multiple versions (person.tags)
        """
        tags = []
        for person in self:
            for ptag in person.tags:
                if not ptag in tags:
                    tags.append(ptag)
                else:
                    #this shouldn't happen, should alert so it can be cleaned up
                    print "WARNING: duplicate tag found in loaded People: %s" % ptag
        return tags
    
class Group(object):
    """
    aka band
    for storing details related to a group of People who work together
    """
    pass


