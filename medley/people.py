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
from __future__ import print_function
from __future__ import absolute_import
#from future import standard_library
#standard_library.install_aliases()
from builtins import str
from builtins import input
from builtins import object
import os, re, json, urllib.request, urllib.parse, urllib.error

from .collector import Cluster
from .helpers import save_json, load_json
from .scraper import download_images

from moments.tag import to_tag
from moments.timestamp import Timestamp


from .person import Person

# create_person and Person moved to person.py

# TODO:
# convert this to a hash / dictionary
class People(list):
    """

    Data for people is stored in directories.
    'source' is the parent directory that holds those folders

    object to load all Person objects into
    to facilitate Person lookup based on tag

    see also: collector.cluster
    similar idea, but rather than holding a list of tag strings
    this holds a list of Person objects.

    also no concept of bins/groups/clusters here... one big list
    use a cluster for sorting

    very similar to a CollectionSummary too
    """
    def __init__(self, source, people_file, term='', debug=False):
        """
        source is where the details are stored
        people_file is where a cloud file of names is
        may be separate locations

        pass in the people term from the config
        """
        self.debug = debug
        if self.debug:
            print("Debugging enabled")

        self.root = source
        # this may not be the case...
        # better to pass this value in
        #self.meta_root = os.path.join(self.root, 'meta')
        #self.meta_root = meta_root
        # if not os.path.exists(self.meta_root):
        #     self.meta_root = None
        #     raise ValueError("Could not find meta root in: %s" % source)
        self.people_file = people_file

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
        #self.cloud_file = os.path.join(self.meta_root, "people.txt")
        if not os.path.exists(self.people_file):
            raise ValueError("Could not find cloud file: %s" % self.people_file)

        #this loads the cluster:
        self.cluster = Cluster()
        self.cluster.from_cloud(self.people_file, term)

    def load(self, root=None):
        """
        look at all directories and load the corresponding person object
        """
        print("Looking for people in: ", self.root)
        # this doese not seem to work... skips everything
        # options = os.scandir(self.root)
        options = os.listdir(self.root)
        if 'meta' in options:
            options.remove('meta')

        if self.debug:
             print("Options:", options)

        missing = []
        # print(options)
        for option in options:
            path = os.path.join(self.root, option)

            if self.debug:
                print("path", path)

            # new pattern where large collections are broken up
            # in subdirectories (currently alphabetical)
            if len(option) == 1:
                sub_options = os.scandir(path)
                for sub_option in sub_options:
                    sub_path = os.path.join(path, sub_option)
                    if self.debug:
                        print("sub_path", sub_path)
                    person = Person(sub_path, debug=self.debug)
                    self.append(person)
            else:
                # sometimes paths are updated, but content takes time to migrate
                # should catch this and alert someone to update accordingly
                # try:
                if not re.search('.list', path):
                    person = Person(path, debug=self.debug)
                    self.append(person)
                else:
                    print("Skipping:", path)
                # except:
                #    missing.append(option)

        #if self.debug:
        #    print "People loaded: "
        #    self.summary()

        if missing:
            for item in missing:
                matches = self.get(item)
                if len(matches):
                    print("MISSING: %s, please move to: %s" % (item, matches[0]))
                else:
                    print("MISSING: %s" % (item))

            raise ValueError("Missing content detected... please fix")

        #may be the case that no local people directories exist
        #could fall back to the cloud / cluster in that case:
        #in this case, don't pass in a root
        #otherwise Person object will try to load it
        options = self.cluster.flatten()
        for option in options:
            if not self.get(option):
                #print("Adding empty person:", option)
                path = os.path.join(self.root, option)

                #sometimes paths are updated, but content takes time to migrate
                #should catch this and alert someone to update accordingly
                #try:
                # don't pass in path here:
                #person = Person(path, debug=self.debug)
                person = Person(tag=option, debug=self.debug)
                #but now that it's initialized,
                #it should be ok to assign it if needed later
                person.root = path
                self.append(person)


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
                tallies.append( (pmatches, person.tag, person) )

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
            if re.match(tag[0], t[2].tag):
                same_start.append(t[2])
            else:
                matches.append(t[2])

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
            print("%s. %s" % (opt_count, option.tag))
            opt_count += 1
        print("")

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
                    print("WARNING: duplicate tag found in loaded People: %s" % ptag)
        return tags

class Group(object):
    """
    aka band
    for storing details related to a group of People who work together
    """
    pass
