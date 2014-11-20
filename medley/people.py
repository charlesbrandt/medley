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
import os, re, copy, json, urllib

from collector import Cluster, CollectionSimple
from content import SimpleContent
from helpers import save_json, load_json

from moments.tag import to_tag
from moments.timestamp import Timestamp

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

        #will use these to automatically set the cutoff from the lists above
        #this can be customized more easily on a group by group basis
        #and then can stay up to date based on the above settings
        self.default_cutoff_tag = ''
        self.default_cutoff = ''

        #path, should be locally available
        #used as default image
        self.image = ''

        #similar to self.content
        #want to load the SimpleContent meta data objects here
        self.photos = []

        #have separated Content and SimpleContent for this purpose
        #this can be a list of jsons (or image paths)
        #also much overlap with moments.path.Image object
        self.photo_order = []

        #will depend on content type:
        #e.g. sounds like, looks like, etc...
        self.similar_to = ''

        #correspond to main cluster group?
        self.rating = ''
        self.quote = ''

        #this is a good place to store content / collection specific data
        #just put everything in a dictionary,
        #then json.dumps value before saving
        self.notes = ''

        #place to keep track of play counts, last visit, etc
        #use similar to notes?
        self.history = ''

        #verified links only
        self.links = ''

        if source:
            #drive dir
            if debug:
                print "using %s as source" % source
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
        #when root is sent from People object, tag is included:
        #return os.path.join(self.root, self.tag)
        return self.root

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
        temp_d.pop("photos", None)
        temp_d.pop("matches", None)
            
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
        #print "Saving: %s to %s" % (temp_d, dest_file)
        save_json(dest_file, temp_d)
        

    def load(self, root=None):
        source_file = self.make_path(root)
        result = load_json(source_file)

        #don't always want to load a cached root,
        #especially when it has been passed in...
        #delete unless it's necessary at some point (can re-enable then)
        del result['root'] 
        
        if self.debug:
            print "Loaded: %s" % result
        self.__dict__.update(result)

    #making this a separate call...
    #when loading people, load() is called
    #don't want to scan for content in that case...
    #only when it is requested
    def load_content(self, debug=False):
        md = self.main_dir()
        #print "Looking for contents in: %s" % md

        #scan for local content directories here
        self.contents = CollectionSimple(root=md)
        #ok to use collection for walking here.
        self.contents.rescan(ignores=['photos'], debug=debug)

        #check self.content_order
        #apply order to contents
        #place any new items at the beginning of the list

        #print self.contents

        found = self.contents.apply_order(self.content_order, debug=debug)

        #update/adjust any cutoffs that are set
        #so that new items don't mess up the orders
        #that were previously (manually) set
        if found and self.cutoffs:
            cutoff_list = self.cutoffs.split(',')
            new_list = []
            for item in cutoff_list:
                #might be '' if extra commas in cutoffs string...
                #can ignore those
                if item:
                    new_item = int(item) + found
                    new_list.append(str(new_item))

            self.cutoffs = ','.join(new_list)

        #update our stored content_order accordingly
        #update order with anything new
        self.content_order = self.contents.get_order()
        if debug:
            print self.content_order

        #update the count:
        self.count = len(self.contents)


        #similar process for photos:
        #print "Looking for photos:"
        photo_dir = os.path.join(self.main_dir(), 'photos')
        self.photos = CollectionSimple(root=photo_dir)
        #this is customized for content being in subdirs
        #self.photos.rescan(debug=True)

        json_check = re.compile('.*\.json$')
        for root,dirs,files in os.walk(photo_dir):
            for f in files:
                if json_check.search(f):
                    json_file = os.path.join(root, f)
                    photo = SimpleContent(json_file)
                    self.photos.append(photo)

                    
        #photos = self.photos.apply_order(self.photo_order, debug=debug)
        new_group = []
        for item in self.photo_order:
            for content in self.photos:
                content_path = os.path.join(content.base_dir, content.filename)
                if content_path == item:
                    if debug:
                        print "adding %s to new list" % item
                    if not content in new_group:
                        new_group.append(content)
                    self.photos.remove(content)

        #anything not in order list should be added to the beginning
        #which means adding the new_group to the end of anything that is left
        self.photos.extend(new_group)
        
        #self.photo_order = self.photos.get_order()
        order = []
        for item in self.photos:
            content_path = os.path.join(item.base_dir, item.filename)
            if not content_path in order:
                order.append(content_path)
        self.photo_order = order

        self.save()

    def apply_cutoffs(self):
        """
        make a new attribute, self.cutoff_groups
        and use self.cutoffs to create the groups
        """
        cur_pos = 0
        self.cutoff_groups = {}
        #without both of these, can't make groups:
        if self.cutoffs and self.cutoff_tags:
            cutoffs = self.cutoffs.split(',')
            cutoff_tags = self.cutoff_tags.split(',')
            for index, item in enumerate(cutoffs):
                tag = cutoff_tags[index]
                self.cutoff_groups[tag] = self.contents[cur_pos:int(item)]
                cur_pos = int(item)
            #print self.cutoff_groups
        
    def update_default(self, new_tag):
        """
        update our default tag
        rename our directory and main meta file accordingly
        """
        if not self.root:
            raise ValueError, "No root specified: %s" % self.root
        
        new_dir = os.path.join(os.path.dirname(self.root), new_tag)
        print "New dir: ", new_dir
        if os.path.exists(new_dir):
            raise ValueError, "Destination exists: %s (from %s)" % (new_dir, self.tag)

        original_file = self.make_path()
        #original_dir = os.path.join(self.root, self.tag)

        new_name = "%s.json" % new_tag
        new_file = os.path.join(self.root, new_name)
        print "renaming: %s, %s" % (original_file, new_file)
        #rename the file first, to make paths easier
        os.rename(original_file, new_file)
        
        #now move the directory
        #os.rename(original_dir, new_dir)
        os.rename(self.root, new_dir)

        self.root = new_dir
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
            if debug:
                print "Loading content for: %s" % (self.tag)
            self.load_content(debug=debug)
            if debug:
                print self.to_dict()
                
            #can only do something if we have some content
            if len(self.photos):
                first = self.photos[0]
                self.image = os.path.join(first.drive_dir, first.base_dir, first.filename)
                
            elif len(self.contents):
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

    def download_photos(self, urls, tags=[]):
        """
        take a list of urls
        must be the image only (won't search a page)
        download the image
        create a SimpleContent representation for the image
        save both local to the person's meta data directory (/photos)

        using urllib.urlretrieve directly
        see also scraper.Scraper.download()
        """
        photos_path = os.path.join(self.root, 'photos')
        if not os.path.exists(photos_path):
            os.makedirs(photos_path)

        #for url in urls[:1]:
        for url in urls:
            if url:
                print
                print url
                #find original filename... should be in the url
                path_parts = url.split('/')
                suffix_parts = path_parts[-1].split('?')
                more_parts = suffix_parts[0].split(':')
                file_name = more_parts[0]
                
                file_name = file_name.replace(' ', '_')
                file_name = file_name.replace('%20', '_')
                file_name = file_name.replace('(', '')
                file_name = file_name.replace(')', '')
                
                #print file_name
                name_parts = file_name.split('.')

                #if the name is generic, at least name it for the person:
                generics = ['original', 'temp', 'photo', 'image', 'picture']
                for option in generics:
                    if re.match(option, name_parts[0], re.I):
                        print "Updating: %s to %s" % (file_name, self.tag)
                        name_parts[0] = self.tag

                extension = name_parts[-1].lower()
                if not extension in [ 'jpg', 'jpeg', 'png', 'gif', 'tif' ]:
                    #just give it something
                    print "Unrecognized extension: %s, adding .jpg" % (extension)
                    name_parts.append('jpg')

                file_name = '.'.join(name_parts)

                download = os.path.join(photos_path, "temp.image")
                if os.path.exists(download):
                    print
                    print url
                    print download
                    raise ValueError, "Temp image already exists. Not overwriting"

                #print download

                #go ahead and download it now:
                urllib.urlretrieve(url, download)

                download_size = os.path.getsize(download)

                #now move the downloaded file into place...
                cur_name = file_name
                existing = True
                duplicate = False
                index = 1
                #loop until we figure out if we already have it,
                #or find a valid new file name
                while existing:
                    new_dest = os.path.join(photos_path, cur_name)
                    if os.path.exists(new_dest):
                        #if the file_name already exists,
                        #check if it is the same (compare file size)
                        dest_size = os.path.getsize(new_dest)
                        if download_size == dest_size:
                            #if its the same simply delete the temp one...
                            print "Already had: %s" % url
                            os.remove(download)
                            existing = False
                            duplicate = True
                        else:
                            #if not, create a new name for it (and try again)
                            prefix = "%s-%04d" % (self.tag, index)
                            name_parts[0] = prefix
                            cur_name = '.'.join(name_parts)
                            index += 1
                    else:
                        #found one that will work
                        existing = False

                if not duplicate:
                    #otherwise
                    #move to safe filename,
                    os.rename(download, new_dest)

                #then create appropriate json file for meta data
                content = SimpleContent()
                content.drive_dir = self.root
                content.base_dir = 'photos'
                content.filename = cur_name
                content.added = Timestamp()
                content.tags = tags
                content.sites.append(url)
                content.people.append(self.tag)
                content.make_hash()

                #make sure we have an extension:
                if len(name_parts) > 1:
                    name_parts[-1] = 'json'
                else:
                    name_parts.append('json')
                json_file = '.'.join(name_parts)
                content.json_source = os.path.join(self.root, 'photos', json_file)
                content.save()

                #don't forget to add the photo to our collection
                relative = os.path.join('photos', cur_name)
                if not relative in self.photo_order:
                    self.photo_order.append(relative)
                    self.save()

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
        self.debug = debug

        self.root = source
        self.meta_root = os.path.join(self.root, 'meta')
        if not os.path.exists(self.meta_root):
            self.meta_root = None
            raise ValueError, "Could not find meta root in: %s" % source
            
        ## if self.debug:
        ##     print source
        ## options = os.listdir(source)
        ## if self.debug:
        ##     print options

        ## self.root = source
        ## if 'meta' in options:
        ##     self.meta_root = os.path.join(self.root, 'meta')
        ## else:
        ##     #should use meta root, but fail if it doesn't exist
        ##     #or could create it here...
        ##     #concerned that that may cause recursive dirs if meta root passed in
        ##     self.meta_root = None
        ##     raise ValueError, "Could not find meta root in: %s" % source
        
        ## options = os.listdir(self.meta_root)
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
                person = Person(path, debug=self.debug)
                self.append(person)
            except:
                missing.append(option)
                
        #if self.debug:
        #    print "People loaded: " 
        #    self.summary()

        if missing:
            for item in missing:
                matches = self.get(item)
                if len(matches):
                    print "MISSING: %s, please move to: %s" % (item, matches[0])
                else:
                    print "MISSING: %s" % (item)

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


