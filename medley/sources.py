# ----------------------------------------------------------------------------
# moments
# Copyright (c) 2009-2010, Charles Brandt
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ----------------------------------------------------------------------------

import os, re, codecs

from moments.journal import Journal
from moments.timestamp import Timestamp
from moments.moment import Moment
from moments.association import Association
from moments.tag import Tags
from moments.path import load_journal, Path

"""
To load an m3u file into a python object:

from mindstream import sources....

might want to look at medley.marks.M3U instead

Items is probably the most useful object in this module.

"""

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
        self._position = position
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

    def _get_position(self):
        return self._position
    def _set_position(self, p):
        self._position = self.check(p)
    position = property(_get_position, _set_position)
    
##     def set(self, position):
##         """
##         would be nice if this just overrides the default set
##         TODO: look up overriding that, maybe check moments.timestamp
##         """
##         self.position = self.check(position)


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
        but does not actually increment the position
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
        but does not actually increment the position
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
        changes the actual position variable
        """
        self.position = self.next(value)
        return self.position

    def decrement(self, value=1):
        """
        changes the actual position variable
        """
        self.position = self.previous(value)
        return self.position

class Items(list):
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
        if items:
            self.current = self.get()
        else:
            #if nothing was sent, be sure to initialize current later!
            self.current = None

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
    def get(self, position=None):
        """
        get calls will not change our position
        """
        #make sure position's length is always current:
        self.update()
        
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

    def get_previous(self):
        return self.get(self._position.previous())

    def get_next(self):
        if self.new:
            self.new = False
            return self.get()
        else:
            return self.get(self._position.next())

    def go(self, position=None):
        """
        go calls will update the local position object
        """
        item = self.get(position)
        if position is not None:
            #whew!  this is a tricky line...
            #setting the position object's internal position:
            self._position.position = position
        self.current = item
        return item

    def go_next(self):
        return self.go(self._position.next())
        
    def go_previous(self):
        return self.go(self._position.previous())

    #maybe rename to update_length to avoid confusion with replace functionality
    def update(self):
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
    

    ## def sort(self, *args, **kwargs):
    ##     ## The sort() method takes optional arguments
    ##     ## for controlling the comparisons.

    ##     ## cmp specifies a custom comparison function of two arguments
    ##     ## (list items)
    ##     ## which should return a negative, zero or positive number
    ##     ## depending on whether the first argument is considered
    ##     ## smaller than, equal to, or larger than the second argument:
    ##     ##     "cmp=lambda x,y: cmp(x.lower(), y.lower())"

    ##     ## key specifies a function of one argument
    ##     ## that is used to extract a comparison key from each list element:
    ##     ##     "key=str.lower"

    ##     ## reverse is a boolean value.
    ##     ## If set to True, then the list elements are sorted
    ##     ## as if each comparison were reversed.

    ##     ## In general, the key and reverse conversion processes
    ##     ## are much faster than specifying an equivalent cmp function.
    ##     ## This is because cmp is called multiple times
    ##     ## for each list element
    ##     ## while key and reverse touch each element only once.
        
    ##     self.sort(*args, **kwargs)

class Source(object):
    """
    A single media object.
    
    an object to formalize the items in the list
    being used in the pyglet based player script

    A Source holds the following:
    media:  a path representing the object, can be local or eventually remote
    jumps:  a list of times for marking transitions, etc
    entry:  the original entry that the source was created from
    """
    def __init__(self, path=None):
        p = Path('./')
        if type(path) == type(p):
            self.path = path
        elif path:
            self.path = Path(path)
        else:
            #print "no object in source!"
            self.path = None
        self.jumps = Jumps()
        self.entry = None

    def __str__(self):
        return self.as_moment().render()

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

    def as_key(self):
        """
        convert a source item
        (that can have up to 3 elements... file, times, entry)
        into an item suitable for a key in a dictionary
        """
        if self.jumps:
            key = ( self.path, tuple(self.jumps) )
        else:
            key = ( self.path )
        return key

def sorter(source):
    p = str(source.path)
    #print p
    return p

class Sources(Items):
    """
    A collection of Source objects
    and a destination path for the logs generated

    aka Playlist, Medialist
    """
    def __init__(self, items=[], log_path=None):
        Items.__init__(self, items)
        if log_path is None:
            self.log_path = '/c/logs/transfer'
        else:
            self.log_path = log_path

    def add_if_new(self, source):
        if not self.has_path(source.path):
            self.append(source)
            return True
        else:
            print "Already have: %s" % source.path
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
        cur_item = self.get()
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
    
class Converter(object):
    """
    Sources generator
    
    a collection of routines used to convert to and from a Sources list

    approaches Sources generation from many different levels

    rather than bog down and clutter the Sources object directly
    can just generate or convert it here
    """
    
    def __init__(self, path=None, sources=None):
        """
        accept a path as the source
        generate the corresponding Sources object

        probably a good idea to pass sources in, so that when Converter
        is destroyed, sources doesn't go with it

        if that's the case, makes sense,
        but seems that returning souce should keep it around in caller
        """
        self.path = path

        #if path is not None:
            
        ## if sources is None:
        ##     self.sources = Sources()
        ## else:
        ##     self.sources = sources

    def from_file(self, path=None, sort=False):
        """
        the default way to try to load a file
        can add some intelligence based on file extensions here
        """
        if path is None:
            if self.path is None:
                raise ValueError, "Need a filename to load from file"
            else:
                path = self.path

        sources = self.from_journal(path, sort)
        return sources
            

    def from_entry(self, entry):
        """
        take one journal entry
        and look for Sources items within it
        """
        sources = Sources()

        #print "ENTRY: %s" % entry.render()
        for line in entry.data.splitlines():
            source = Source()
            #print "Pre Source: %s, entry: %s" % (source, source.entry.render())
            if re.search("\ -sl\ ", line):
                #this requires the first 3 items to be:
                # # -sl [nums] [file]
                # otherwise parts will be off
                # see replace.txt
                parts = line.split(' ', 3)
                try:
                    sl_pos = parts.index('-sl')
                except:
                    print "SL found, but incorrect format:"
                    print e.render()
                    exit()
                jumpstr = parts[sl_pos+1]
                jumps = Jumps(jumpstr)
                
                try:
                    source_file = parts[sl_pos+2]
                except:
                    print "no source file in parts: %s" % parts
                    print line
                    print

                #get rid of surrounding quotes here
                source_file = source_file.replace('"', '')
                
                source.path = source_file
                source.jumps = jumps
                source.entry = entry
                #print "adding source: %s" % source
                sources.append( source )
                
            elif line.strip():
                #this will not work with entries that have file paths
                #and other comments/text in them:

                #'# -sl ' should be caught by previous case
                #could verify that line starts with either a '/' 'http:'
                source_file = line.strip()
                if re.match('^media', source_file):
                    source_file = source_file.replace('media/', '')
                    source_file = '/c/' + source_file
                #elif re.match('^graphics', source_file):
                
                ## if re.match('^/', source_file):
                ##     source = Source()
                ##     source.path = source_file
                ##     source.entry = entry
                ##     #print "adding source: %s" % source
                ##     self.sources.append( source )
                ## else:
                ##     print "Non Source: %s" % source_file

                source.path = Path(source_file)
                source.entry = entry
                #print "entry: %s" % entry.render()
                #print "adding source: %s" % source
                sources.append( source )

            #if source.entry:
            #    print "Source: %s, entry: %s" % (source, source.entry.render())

                
        return sources

    def from_entries(self, entries, sources=None):
        """
        take a list of moments/entries
        for each line in the entry
        see if it will work as a playlist item
        add if so
        """
        if not sources:
            sources = Sources()
        for e in entries:
            sources.extend(self.from_entry(e))
            
        sources.update()
        return sources

    #def condense_and_sort(self, destination=None):
    def condense_and_sort(self, sources=None):
        """
        whatever is in the list,
        count the number of times items show up in the list
        (return the frequency of those items)
        and sort items by that frequency
        and return a condesed list in that order
        """
        #if destination is None:
        destination = Sources()
        
        ## freq = Association()
        ## for i in pl:
        ##     freq.associate(i, i[0])
        ## item_lists = freq.items_by_frequency()
        ## new_list = []
        ## #now have a list of:
        ## #[ [file_path, list_of_original_playlist_items], ..]
        ## for i in item_lists:
        ##     longest = ['', []]
        ##     for playlist_item in i[1]:
        ##         if len(playlist_item[1]) >= len(longest[1]):
        ##             longest = playlist_item
        ##     #print len(longest[1])
        ##     new_list.append(longest)

        tally = {}

        print "Starting size: %s" % len(sources)

        #at this point we will be losing any entry associated
        #in order to condense
        #this will also lose any tag data
        #we can look up one of these entries later
        #no guarantee which one will be reassociated
        # could go through all entries later and tally up tags there
        # don't want to do that just yet though
        for i in sources:
            #print i
            #print type(i)
            i.jumps.sort()
            key = i.as_key()

            if tally.has_key(key):
                tally[key] += 1
            else:
                tally[key] = 1

        #get the keys and values
        items = tally.items()

        #convert top items to lists instead of default tuple returned by dict
        new_items = []
        for i in items:
            new_items.append( list(i) )
        items = new_items

        #NOTE ON WHAT IS STORED IN THE KEY:
        ## if self.jumps:
        ##     key = ( self.path, tuple(self.jumps) )
        ## else:
        ##     key = ( self.path )
        ## return key
        #
        #AND ITEMS CONTAIN LISTS OF (KEY, VALUE)
        #where value is the number of times a key appeared

        #condense items:
        condensed = items[:]
        for i in items:
            # see if we have jumps to consider
            if len(i[0]) > 1:
                #could be more than one condensed(c) that has jumps as subset...
                #should stop after we find one that matches
                #(hence using 'while' instead of 'for')
                #if we find a subset, add the count of the subset
                #to the count of the superset
                #and then remove the subset from the condensed list
                pos = 0
                match = False
                while not match:
                    c = condensed[pos]
                    #if condensed.key.path == item.key.path
                    #and we have jumps to consider:
                    if (c[0][0] == i[0][0]) and (len(c[0]) > 1):
                        #both have times
                        #check if either is a subset of the other
                        cset = set(c[0][1])
                        iset = set(i[0][1])
                        if len(cset.difference(iset)) == 0:
                            #same set!
                            #could be the same item
                            pass
                        elif cset.issubset(iset):
                            #update tally i in condensed
                            pos = condensed.index(i)
                            condensed[pos][1] += c[1]
                            print "found subset: %s of: %s. current length: %s" % ( cset, iset, len(condensed))
                            condensed.remove(c)
                            print "new length: %s" % len(condensed)
                            match = True
                        elif iset.issubset(cset):
                            #update tally i in condensed
                            pos = condensed.index(c)
                            condensed[pos][1] += i[1]
                            print "found subset: %s of: %s. current length: %s" % ( iset, cset, len(condensed))
                            condensed.remove(i)
                            print "new length: %s" % len(condensed)
                            match = True
                        else:
                            #print "times didn't match"
                            pass
                    pos += 1
                    if pos >= len(condensed):
                        #maybe no match, exit while loop
                        match = True

            #must not have any jumps in this playlist item
            else:
                #in this case, the list should have been the same
                pass
            
        items = condensed
        print "After Condensing: %s" % len(items)

        # see Items.sort()

        #need to sort based on second item in the list, not the first...
        #not sure how to do this with sort...
        #I think there is a better way than this:
        #swap positions:
        new_items = []
        for i in items:
            new_items.append( (i[1], i[0]) )
        new_items.sort()
        new_items.reverse()
        items = []
        for i in new_items:
            items.append( i[1] )

        print "After Sorting: %s" % len(items)

        #re-assign the original entry with an item if we can
        #
        #this will not catch the case when jumps were merged into a larger set
        #will lose entry association in that case
        for i in sources:
            key = i.as_key()
            if key in items:
                pos = items.index(key)
                items[pos] = [ i.path, i.jumps, i.entry ]

        print "After Adding original entry back: %s" % len(items)


        #regenerate a new Sources object:
        for i in items:
            source = Source()
            source.path = i[0]
            if len(i) > 1:
                source.jumps = i[1]
            if len(i) > 2:
                source.entry = i[2]
            destination.append(source)

        #should be smaller or the same if condensing and sorting is working:
        print "Ending size: %s" % len(destination)

        destination.update()
        return destination
    
    def from_m3u(self, filename=None, sources=None):
        if not filename:
            filename = self.path
        f = codecs.open(filename, encoding='latin_1')

        if not sources:
            sources = Sources()
                        
        for line in f.readlines():
            line = unicode(line)
            if line.startswith('#') or len(line.strip()) == 0:
                pass
            else:
                sources.append(Source(path=line.strip()))
                #self.append(line.strip())

        f.close
        sources.update()
        return sources

    def from_copy_all_urls(self, data):
        """
        parse a buffer that contains output from copy all urls as a list

        for now skipping title lines... will need those for export
        """
        
        for line in data.splitlines():
            if line.startswith('http://') or line.startswith('/'):
                self.append(line.strip())

    def from_journal(self, path, sources=None, sort=False):
        """
        use from_entries, and condense_and_sort()
        """
        j = load_journal(path)
        print len(j)
        print j
        for i in j:
            print i.render()

        sources = self.from_entries(j, sources)
            
        print len(sources)
        if sort:
            #condense and sort will change the order of an entry list
            new_sources = self.condense_and_sort(sources)
            return new_sources
        else:
            return sources

    def save(self):
        pass

    def to_journal(self, destination, sources, tags=[], skip_dupes=False):
        """
        use from_entries, and condense_and_sort()
        """
        j = load_journal(destination)
        print len(j)
        print j

        if skip_dupes:
            j.associate_data()
            for source in sources:
                if not j.datas.has_key(str(source.path)+'\n\n'):
                    moment = source.as_moment()
                    moment.tags.union(tags)
                    j.update_entry(moment)
        else:
            for source in sources:
                moment = source.as_moment()
                moment.tags.union(tags)
                j.update_entry(moment)
                
        j.to_file(destination)

    def to_links(self, prefix='/dir'):
        links = ''
        for i in self:
            obj = self.get_object(i)
            links += url_for(obj.custom_relative_path(prefix=prefix), qualified=True)
            links += "\r\n"
        return links

    def to_m3u(self, sources, verify=True, flat=False, remote=False):
        m3u = "#EXTM3U\r\n"
        for s in sources:
            if (verify and s.path.exists()) or (not verify):
                #obj = self.get_object(i)
                i = str(s.path)
                #could use an ID3 library to load this information here:
                length = 0
                artist = ""
                title = os.path.basename(i)
                m3u += "#EXTINF:%s,%s - %s\r\n" % (length, artist, title)
                if remote:
                    m3u += url_for(obj.custom_relative_path(prefix="/sound"), qualified=True)
                elif flat:
                    m3u += s.path.filename
                else:
                    m3u += i

                m3u += "\r\n"
            else:
                print "Ignoring. Item not found: %s" % s.path
        return m3u

    def to_xspf(self, filename=None):        
        xspf = StringIO.StringIO("Hello")
        xml = XmlWriter(xspf, indentAmount='  ')

        xml.prolog()
        xml.start('playlist', { 'xmlns': 'http://xspf.org/ns/0/', 'version': '1' })
        xml.start('trackList')

        for line in self:
            #line = line.rstrip('\n')

            url = None
            if line.startswith('http://'):
                url = line
            else:
                obj = self.get_object(line)
                if obj:
                    url = url_for(obj.custom_relative_path(prefix="/sound"), qualified=True)
                    #url = url_for(url_escape(obj.custom_relative_path(prefix="/sound")), qualified=True)
                #url = 'file://' + urllib.pathname2url(line)

            if url:
                xml.start('track')
                xml.elem('location', url)
                xml.elem('title', os.path.basename(line))
                #if options.add_annotation:
                #        xml.elem('annotation', createAnnotation(url))

                xml.end() # track

        xml.end() # trackList
        xml.end() # playlist
        
        xspf.seek(0)
        return xspf.read()

class Jumps(Items):
    def __init__(self, comma='', items=[]):
        Items.__init__(self, items)
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
