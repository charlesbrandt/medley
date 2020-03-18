import os
import re
import copy

from .helpers import save_json, load_json
from .collector import Cluster, CollectionSimple
from .content import SimpleContent

def create_person(name_tag, people, cluster_pos, root, skipped, ambi, auto_create=True, letter_index_dirs=True):
    """
    a People object is loaded in the caller

    then this function takes the name_tag
    look in people to see if there is anything similar
    if not create it
    if similar exists, prompt the user for what to do

    there are other checks that could be done, depending on the data set
    but this is usually a low common denominator

    letter_index_dirs specifies if the first letter should be used as a parent directory. This is useful for breaking up large collections.
    """

    if letter_index_dirs:
        dest_path = os.path.join(root, name_tag[0], name_tag)
    else:
        dest_path = os.path.join(root, name_tag)

    # see if there is anything similar:
    options = people.search(name_tag)
    
    # # some options may not exist yet...
    # # filter out to show ones that have directories?
    # options = []
    # for item in all_options:
    #     if item.check_path():
    #         options.append(item)
            
    if (not options) and auto_create:

        #make a new Person object
        print("Creating new: %s" % name_tag)
        p = Person(tag=name_tag)
        p.rating = cluster_pos
        p.save(dest_path)
        people.append(p)

    else:
        #there must be similar options
        #we should manually review these options
        #to see if name_tag should be merged with an existing person
        # (check if it is a better default)
        #or create a new Person
        finished = False
        while not finished:
            print("")
            print("%s matched:" % name_tag)
            opt_count = 0
            for option in options:
                if not option.tag == name_tag:
                    print("%02d. %s (exists? %s)" % (opt_count, option.tag, option.check_path()))
                opt_count += 1
                #print options

            #http://docs.python.org/2/library/functions.html#raw_input
            #could also consider:
            #http://docs.python.org/2/library/cmd.html
            #via http://stackoverflow.com/questions/70797/python-and-user-input
            action = input("(M)erge with existing, create (N)ew, mark as (A)mbiguous, or (S)kip? ")
            number_match = False
            number = -1
            try:
                number = int(action)
            except:
                pass
            else:
                number_match = True

            if (action.lower() == 'm') or number_match:
                if len(options) == 1:
                    number = 0
                elif not number_match:
                    numstr = input("Merge with which number? ")
                    number = int(numstr)

                if number < len(options):
                    try:
                        prompt = u"Make '" + name_tag + u"' the default? (y/N) "
                        primary = input(prompt)
                    except:
                        prompt = u"Make '" + u"' the default? (y/N) "
                        primary = input(prompt)

                    dest = options[number]
                    dest.tags.append(name_tag)
                    dest.save()

                    if (not primary) or primary.lower() == 'n':
                        print("Merged %s to %s tags (%s)" % (name_tag, dest.tag, dest.tags))
                        finished = True
                    elif primary.lower() == 'y':
                        dest.update_default(name_tag)
                        #dest.tag = name_tag
                        #TODO:
                        #move dest to a new directory named name_tag
                        #remove old directory
                        finished = True
                    else:
                        print("Unknown response: %s" % primary)
                else:
                    print("Number out of range (%s): %s" % (len(options), number))
            elif action.lower() == 'n':
                #make a new Person object
                p = Person(tag=name_tag)
                p.rating = cluster_pos
                p.save(dest_path)
                people.append(p)
                finished = True
                print("Created %s at %s" % (name_tag, dest_path))

            elif action.lower() == 's':
                skipped.append(name_tag)
                print("Skipping: %s" % name_tag)
                finished = True

            elif action.lower() == 'a':
                ambi.add_at(name_tag, cluster_pos)
                #added ambiguous_file as .source attribute on init
                #ambi.save(ambiguous_file)
                ambi.save()
                print("Marked Ambiguous: %s" % name_tag)
                finished = True

            else:
                print("Unknown response: %s" % action)


class Person(object):
    def __init__(self, source='', tag='', debug=False):
        """
        set up the basics
        """
        #for disply purposes only
        self.name = ''

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

        self.debug = debug
        # if self.debug:
        #    print("Finished initializing:", self.root)


        #print("source:", source)
        if source:
            #drive dir
            if debug:
                print("using %s as source" % source)
            self.root = source
            self.load()
        else:
            self.root = ''



    def __repr__(self):
        return "Person: %s" % self.tag

    def __lt__(self, other):
        return self.tag < other.tag
    
    def split_tag(self):
        return self.tag.replace('_', '+')

    #TODO:
    #this might be better as a property
    def main_dir(self):
        #when root is sent from People object, tag is included:
        #return os.path.join(self.root, self.tag)
        return self.root

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

    def check_path(self):
        if not self.root:
            raise ValueError("No root specified: %s" % self.root)

        return os.path.exists(self.main_dir())
        
    def make_path(self, root=None):
        if root:
            self.root = root

        main_dir = self.main_dir()
        if not self.check_path():
            os.makedirs(main_dir)

        if not self.tag:
            self.tag = os.path.basename(self.root)
            #could also look for any json file here using medley.helpers
            #but should fail if names are not kept in sync

        filename = "%s.json" % self.tag
        main_file = os.path.join(main_dir, filename)
        return main_file

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
            raise ValueError("Need a root to know where to save: %s" % self.root)

        dest_file = self.make_path(self.root)
        #print dest_file
        temp_d = self.to_dict()

        print()
        print("save:")
        print(temp_d['photo_order'])
        print()

        #save_json(dest_file, self.__dict__)
        #print "Saving: %s to %s" % (temp_d, dest_file)
        save_json(dest_file, temp_d)


    def load(self, root=None):
        source_file = self.make_path(root)
        if os.path.exists(source_file):
            result = load_json(source_file)
            #don't always want to load a cached root,
            #especially when it has been passed in...
            #delete unless it's necessary at some point (can re-enable then)
            del result['root']
        else:
            print("No json source:", source_file)
            result = {}


        # if self.debug:
        #     print("Loaded: %s" % result)
        self.__dict__.update(result)

    #making this a separate call...
    #when loading people, load() is called
    #don't want to scan for content in that case...
    #only when it is requested
    def load_content(self, debug=False):
        md = self.main_dir()
        if os.path.exists(md):
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
                print(self.content_order)

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
                    #when sending from javascript,
                    #always includes a '/' between the two,
                    #even if base_dir is empty... os.path.join won't...
                    #going manual here so things match
                    #content_path = os.path.join(content.base_dir, content.filename)
                    content_path = content.base_dir + '/' + content.filename
                    if content_path == item:
                        if debug:
                            print("adding %s to new list" % item)
                        if not content in new_group:
                            new_group.append(content)
                        self.photos.remove(content)

            #anything not in order list should be added to the beginning
            #which means adding the new_group to the end of anything that is left
            self.photos.extend(new_group)

            #self.photo_order = self.photos.get_order()
            order = []
            for item in self.photos:
                #content_path = os.path.join(item.base_dir, item.filename)
                content_path = item.base_dir + '/' + item.filename
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
            raise ValueError("No root specified: %s" % self.root)

        new_dir = os.path.join(os.path.dirname(self.root), new_tag)
        print("New dir: ", new_dir)
        if os.path.exists(new_dir):
            raise ValueError("Destination exists: %s (from %s)" % (new_dir, self.tag))

        original_file = self.make_path()
        #original_dir = os.path.join(self.root, self.tag)

        new_name = "%s.json" % new_tag
        new_file = os.path.join(self.root, new_name)
        print("renaming: %s, %s" % (original_file, new_file))
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
                print("Loading content for: %s" % (self.tag))
            self.load_content(debug=debug)
            if debug:
                print(self.to_dict())

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
                        print("updating %s image to %s" % (self.tag, self.image))
                    self.save()

                else:
                    if debug:
                        print("No image associate with first content: %s" % self.tag)
                        print("%s contents total" % len(self.contents))

            else:
                if debug:
                    print("No content found for %s" % self.tag)

        else:
            if debug:
                print("Not updating: %s" % self.tag)

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

        people = [ self.tag ]
        alt_name = self.tag

        results = download_images(urls, photos_path, tags, alt_name, people, self.root, 'photos')

        for cur_name in results:
            #don't forget to add the photo to our collection
            relative = os.path.join('photos', cur_name)
            if not relative in self.photo_order:
                self.photo_order.append(relative)
                self.save()
