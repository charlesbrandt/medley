from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from builtins import next
from builtins import object
import os, codecs, re
from .helpers import save_json, load_json
from .content import Content

class Position(object):
    """
    more than just a number of an item
    or index of a list
    
    we just want to hold a position and length

    from this we can determine the number for previous, next
    and provide increment and decrement options

    loop is tracked here

    error checking and representing positions
    """
    def __init__(self, length=0, position=0, loop=True):
        self._index = position
        self._length = length
        self.loop = loop

    def __int__(self):
        return self.position

    def __str__(self):
        return str(self.position)

    def __repr__(self):
        return self.position

    def _get_length(self):
        return self._length
    def _set_length(self, l):
        self.change_length(l)
    length = property(_get_length, _set_length)

    def _get_index(self):
        return self._index
    def _set_index(self, p):
        self._index = self.check(p)
    position = property(_get_index, _set_index)
    
    def end(self):
        """
        the value for the last object
        """
        return self.length-1

    def at_end(self):
        """
        return a boolean value for if our position is equal to the end
        """
        return self.position == self.end()

    def change_length(self, length):
        """
        position needs to know how long the list is
        we can change that later if we don't know the length
        """
        self._length = length
        #go ahead one just to make sure we weren't beyond the new length
        self.decrement()
        self.increment()

    def check(self, position):
        """
        accept a vaule for a position
        check to make sure it falls within the range of acceptable values

        if greater, go to the end
        if less than 0, go to the beginning

        could consider doing a mod operation and taking the remainder as
        the new position.
        """
        if position < 0:
            return 0
        elif position >= 0 and position <= self.end():
            return int(position)
        else:
            return self.end()

    def next(self, value=1):
        """
        gives the position for the next item
        but does not actually increment the index
        """
        if self.position+value >= self.length:
            if self.loop:
                return 0
            else:
                #staying at the end
                #return self.position
                #return self.length-1
                return self.end()
        else:
            return self.position+value
    
    def previous(self, value=1):
        """
        gives the position for the next item
        but does not actually increment the index
        """
        if self.position-value < 0:
            if self.loop:
                #return self.length-1
                return self.end()
            else:
                #staying at the beginning
                #(should be 0 already)
                return 0
        else:
            return self.position-value

    def increment(self, value=1):
        """
        changes the actual index variable
        """
        self.position = self.next(value)
        return self.position

    def decrement(self, value=1):
        """
        changes the actual index variable
        """
        self.position = self.previous(value)
        return self.position

    def debug(self):
        """
        return a string representation of current state
        """
        result = ''
        result += "Position index: %s\n" % self._index
        result += "Length: %s\n" % self._length
        result += "Loop: %s\n" % self.loop
        return result

#previously: (too generic)
#class Items(list):
class PositionList(list):
    """
    generic list with a position associated with it
    position will get updated with call to update()

    otherwise...
    changing the position is left to the caller
    """
    def __init__(self, items=[], position=0):
        list.__init__(self)
        self.extend(items)
        self._position = Position(len(items), position)
        
        #quick way to access the current item directly
        #rather than having get return the value
        #if items:
        #    self.current = self.get()
        #else:
        #    #if nothing was sent, be sure to initialize current later!
        #    self.current = None

        #special case for get_next...
        #if we're new, return 0
        #otherwise... all other rules apply
        self.new = True

    #wrap position object, so that we can assign a new position to the list
    #as though it were an attribute.
    #this simplifies the interface to the list of items.
    def _get_position(self):
        return self._position
    def _set_position(self, p):
        self.go(p)
    position = property(_get_position, _set_position)
    
    #aka get_current?
    #def get(self, position=None):
    def current(self):
        """
        shortcut for get() without a specific position passed in
        """
        return self.get()

    def get(self, position=None):
        """
        get calls will not change our position
        """
        #make sure position's length is always current:
        self.update_length()
        
        #print "Received position: %s" % position
        #print "Current position: %s" % self._position
        #print "Length: %s" % len(self)

        #should we update current here? or use current?
        if position is None:
            #use our current position
            return self[int(self._position)]
        else:
            #checking if position is out of range here:
            return self[self._position.check(position)]

    #changing the interface to be the same as it is with Position object:
    #def get_previous(self):
    def previous(self):
        """
        get the previous item in the list without changing position
        """
        return self.get(self._position.previous())

    #def get_next(self):
    def __next__(self):
        """
        get the next item in the list without changing position
        """
        if self.new:
            self.new = False
            return self.get()
        else:
            return self.get(next(self._position))

    def go(self, position=None):
        """
        go calls will update the local position object
        """
        item = self.get(position)
        if not position is None:
            #whew!  this is a tricky line...
            #setting the position object's internal position:
            self._position.position = position
        #self.current = item
        print(self._position.debug())
        print("passed position: %s" % position)
        return item

    #changing the interface to be the same as it is with Position object:
    #def go_next(self):
    def increment(self):
        """
        go to the next item in the list (and change our position accordingly)
        """
        return self.go(next(self._position))
        
    #def go_previous(self):
    def decrement(self):
        """
        go to the previous item in the list
        (and change our position accordingly)
        """
        return self.go(self._position.previous())

    #maybe rename to update_length to avoid confusion with replace functionality
    #def update(self):
    def update_length(self):
        """
        update the position so it knows our new length
        should be called any time items are added or removed to the list
        """
        self._position.change_length(len(self))

    def replace(self, item):
        """
        replace the item in the current position
        with the item passed in
        """
        self[int(self._position)] = item
    
    def clear(self):
        del self[:]
        self.update_length()
        

#aka
## class Sources(Items):
class Playlist(PositionList):
    """
    Similar to a collection in that it holds a group of Content objects,
    but not geared toward a single source of content.

    Also, not specific to any single playlist format (e.g. M3U).
    
    Because it holds Content objects,
    there is much more meta data available than a typical playlist

    very similar concepts to old mindstream sources module:
    /c/medley/medley/sources.py

    A generic Playlist object

    These may help:
    http://docs.python.org/2/library/collections.html

    Previously:
    A collection of Source objects
    and a destination path for the logs generated

    aka Playlist, Medialist


    consider the best way to handle Segments in a Content object
    for Playlist use:
    Separate copies of Content in the Playlist for each Segment?
      -- be careful not to save that Content object back and overwrite all
         previous segments
    Playlist reorders list of Segments associated with Content
      -- more difficult to split segments of one piece of content in between
         segments of another piece of content, within a list

    also:
    when editing a segment, save changes to main json parent Content


    """
    def __init__(self, items=[], log_path=None, debug=False):
        PositionList.__init__(self, items)
        if log_path is None:
            self.log_path = '/c/logs/transfer'
        else:
            self.log_path = log_path

        #whether or not to update a content's source json file
        #or just make the changes to the list locally
        #
        #generally with a playlist you don't want to update the content source
        #e.g. subtractively limiting content segments to only favorites...
        #     wouldn't want to remove those segments from the content source
        #     just from the current playlist
        #
        #this should not matter if a content object is edited directly
        self.sync_contents = False

        self.debug = debug

    #save and load:
    #use helpers
    #save_json(destination, self[:])
    #and
    #Playlist(load_json(source)) #assuming json contains a list of Contents
    #any other format should be used 

    def set_current(self, item):
        """
        if we have item
        set the position to be that item
        (useful when selecting next item externally)
        """
        self.go(self.index(item))
        #no need to return anything... already have the item

    def add_if_new(self, source):
        if not self.has_path(source.path):
            self.append(source)
            return True
        else:
            print("Already have: %s" % source.path)
            return False

    def has_path(self, path):
        """
        go through all of our items and see if we have the path
        """
        found = False
        for i in self:
            #print "m3u path: %s" % i.path
            #print "chk path: %s" % path
            if str(i.path) == str(path):
                found = True
                break

        return found

    def save(self, destination):
        """
        consider using ContentPointer object here.. (is it useful?)
        """
        items = []
        for content in self:
            json_path = os.path.join(content.path, content.json_source)
            items.append( [json_path, content.segment_id] )

        save_json(destination, items)

    #def load_playlist(fname):
    def load(self, fname, all_contents={}):
        """
        if you want to keep track of all contents loaded,
        pass in a dictionary of all_contents...
        load will update that with any new Content objects,
        and reuse any existing objects from there
        
        originally from medley.player.list_tree.load_playlist(fname)
        
        expects the playlist to hold:
           - the content source path
           - the segment id

        then loads the content from the source, and selects the correct segment
        """
        self.clear()
        
        items = load_json(fname)
        #print items
        contents = []
        for item in items:
            if self.debug:
                print(item)
                print("")
                
            (json_source, segment_id) = item
            if json_source in all_contents:
                if self.debug:
                    print("Matched existing Content object with path: %s" % json_source)
                content = all_contents[json_source]
            else:
                try:
                    if self.debug:
                        print("loading: %s" % json_source)
                    content = Content(json_source)
                    all_contents[json_source] = content
                except:
                    print("removing item. could not load: %s" % json_source)

            #print json_source
            try:
                segment = content.get_segment(segment_id)
            except:
                raise ValueError("Could not locate content... is it still available locally?")
            #print segment.to_dict()
            #print ""
            #print ""
            contents.append(segment)
            
        #return Playlist(contents)
        self.extend(contents)
        #update position_list so it knows
        self.update_length()

    def sort_path(self):
        #self.sort(key=lambda source: str(source.path))
        self.sort(key=sorter)
        
    def log_current(self, add_tags=[]):
        """
        log that a play was just completed
        
        this is very similar to osbrowser.node log_action?

        could move into moments.journal
        would need the log path, the file being logged (or file parent path)
        and the entry to use
        """
        entry = self.now_playing()
        entry.tags.union(add_tags)
        
        #log in default log directory
        j = Journal()
        now = Timestamp(now=True)
        log_name = os.path.join(self.log_path , now.filename())
        j.from_file(log_name)
        j.update_entry(entry)
        j.to_file()

        # log in action.txt for current media's directory
        cur_item = self.current()
        parent_path = os.path.dirname(str(cur_item.path))
        action = os.path.join(parent_path, 'action.txt')
        j2 = Journal()
        j2.from_file(action)
        j2.update_entry(entry)
        j2.to_file()
        
    def now_playing(self):
        """
        return an entry for what is playing
        """
        cur_item = self.get()
        return cur_item.as_moment(new_entry=True)


class ListTree(object):
    """
    hold a hierarchy of playlists and collections
    
    """
    def __init__(self):
        #a place to keep track of all playlists and collections
        #associated with the grouping
        #can be hierarchical
        self.playlists = []
        

        #the goal is to store these for easy loading later
