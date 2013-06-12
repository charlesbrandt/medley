import os, codecs, re

from content import Mark

class M3U(list):
    """
    have come up with many different ways to convert M3U files
    but never an object to represent one natively

    the most simple format is simply a list of strings,
    where each string represents a path to a specific media

    TODO:
    should also support a list of Content objects (both save and load)
    for more complex sorting.
    """
    def __init__(self, source=None):
        self.source = source

        #TODO:
        #marks should be associated with a Content object
        self.marks = Marks()
        if source:
            self.load()

    #TODO:
    #incorporate version that handles marks
    def from_m3u(self, source=None):
        """
        read in the source
        update the "files" dictionary with marks
        """
        if source is None:
            source = self.source

        if source is None:
            raise ValueError, "Need a source sooner or later: %s" % source
        
        print "opening: %s" % source
        #for reading unicode
        f = codecs.open(source, 'r', encoding='utf-8')

        marks_options = []
        for line in f.readlines():
            if re.match("#EXTM3U", line):
                pass
            elif re.match("#EXTINF", line):
                line = line[8:]
                #print line
                length, title = line.split(',')
                #print "length: %s, title: %s" % (length, title)
            elif re.match("#EXTVLCOPT", line):
                #latest bookmarks:
                line = line[21:]
                parts = line.split('},')
                #reset this every time... we only want the last one
                marks_options = []
                for part in parts:
                    part = part.replace('{', '')
                    #print part
                    part = part.replace('}', '')
                    sub_parts = part.split(',')
                    if len(sub_parts) == 3:
                        fullname, fullbytes, fulltime = sub_parts
                        #print fullname, fullbytes, fulltime
                        name = fullname.split('=')[1]
                        bytes = fullbytes.split('=')[1]
                        time = fulltime.split('=')[1]

                        bytes_per_second = 24032.0
                        ms = (float(bytes) / bytes_per_second) * 1000
                        ms = int(ms)

                        ## if int(time) < 0:
                        ##     # need to figure out time based on bytes
                        ##     # sometimes vlc gives negative values 
                        ##     # that doesn't help
                        ##     # also [2012.10.12 11:24:19] 
                        ##     # not just negative values that can be wrong
                        ##     #
                        ##     # this value could change based on encoding:
                        ##     # current bytes per second:
                        ##     # 24069.11418685121107
                        ##     # 24023.08172902288413
                        ##     ms = (float(bytes) / 24032.0) * 1000
                        ##     ms = int(ms)
                        ## else:
                        ##     ms = int(time) * 1000
                        
                    else:
                        raise ValueError, "Unknown number of sub parts in bookmarks: %s" % sub_parts

                    marks_options.append( [ int(ms), name, bytes ] )
            else:
                #must have a filename here
                #now we can process mark options
                location = line
                marks_options.sort()
                for mo in marks_options:
                    ms, name, bytes = mo
                    length_ms = int(length) * 1000
                    details = Mark(name, ms, location, length_ms, bytes=bytes)
                    self.append(details)
                    
        f.close()

        return self

    def load(self, source=None):
        """
        read in the source
        update the "files" dictionary with marks
        """
        if source is None:
            source = self.source

        if source is None:
            raise ValueError, "Need a source sooner or later: %s" % source
        
        print "opening: %s" % source
        #for reading unicode
        f = codecs.open(source, 'r', encoding='utf-8')

        marks_options = []
        for line in f.readlines():
            if re.match("#EXTM3U", line):
                pass
            elif re.match("#EXTINF", line):
                line = line[8:]
                #print line
                #length, title = line.split(',')
                parts = line.split(',')
                length = parts[0]
                title = parts[1]
                #print "length: %s, title: %s" % (length, title)
            elif re.match("#EXTVLCOPT", line):
                #latest bookmarks:
                line = line[21:]
                parts = line.split('},')
                #reset this every time... we only want the last one
                marks_options = []
                for part in parts:
                    part = part.replace('{', '')
                    #print part
                    part = part.replace('}', '')
                    sub_parts = part.split(',')
                    if len(sub_parts) == 3:
                        fullname, fullbytes, fulltime = sub_parts
                        #print fullname, fullbytes, fulltime
                        name = fullname.split('=')[1]
                        bytes = fullbytes.split('=')[1]
                        time = fulltime.split('=')[1]

                        bytes_per_second = 24032.0
                        ms = (float(bytes) / bytes_per_second) * 1000
                        ms = int(ms)

                        ## if int(time) < 0:
                        ##     # need to figure out time based on bytes
                        ##     # sometimes vlc gives negative values 
                        ##     # that doesn't help
                        ##     # also [2012.10.12 11:24:19] 
                        ##     # not just negative values that can be wrong
                        ##     #
                        ##     # this value could change based on encoding:
                        ##     # current bytes per second:
                        ##     # 24069.11418685121107
                        ##     # 24023.08172902288413
                        ##     ms = (float(bytes) / 24032.0) * 1000
                        ##     ms = int(ms)
                        ## else:
                        ##     ms = int(time) * 1000
                        
                    else:
                        raise ValueError, "Unknown number of sub parts in bookmarks: %s" % sub_parts

                    marks_options.append( [ int(ms), name, bytes ] )
            else:
                #must have a filename here
                #now we can process mark options
                location = line.strip()
                marks_options.sort()
                for mo in marks_options:
                    ms, name, bytes = mo
                    length_ms = int(length) * 1000
                    details = Mark(name, ms, location, length_ms, bytes=bytes)
                    self.marks.append(details)
                self.append(location)
                    
        f.close()

        return self

    #TODO:
    #incorporate this version that handles saving marks

    def to_m3u(self, destination="temp.m3u", verify=False):
        f_marks = {}
        self.group_marks_by_file(f_marks)
        m3u = "#EXTM3U\r\n"
        for source in f_marks.keys():
            if (verify and os.path.exists(source)) or (not verify):
                #obj = self.get_object(i)
                #could use an ID3 library to load this information here:
                length = 0
                artist = ""
                title = os.path.basename(source)
                m3u += "#EXTINF:%s,%s - %s\r\n" % (length, artist, title)

                bmarks = []
                for mark in f_marks[source]:
                    bmarks.append(mark.as_m3u())
                bookmarks = ','.join(bmarks)
                m3u += "#EXTVLCOPT:bookmarks=%s\r\n" % bookmarks
                m3u += mark.source

                m3u += "\r\n"
            else:
                print "Ignoring. Item not found: %s" % source

        f = codecs.open(destination, 'w', encoding='utf-8')
        f.write(m3u)
        f.close()
                
        return m3u



    def save(self, destination, verify=True, flat=False):
        """
        TODO:
        this does not yet deal with saving marks
        that can be added as needed
        see marks.to_m3u()
        """
        if destination is None:
            destination = self.source

        if destination is None:
            raise ValueError, "Need a destination sooner or later: %s" % destination
        
        print "opening: %s" % destination
        f = codecs.open(destination, 'w', encoding='utf-8')

        m3u = u"#EXTM3U\r\n"
        for item in self:
            #TODO:
            #debug path with special characters:
            #print item
            #s = Path(item)
            #if (verify and s.exists()) or (not verify):
            if (verify and os.path.exists(item)) or (not verify):
                #could use an ID3 library to load this information here:
                length = 0
                artist = u""
                title = os.path.basename(item)
                #either of these should work as long as no paths
                #have been converted to strings along the way
                #m3u += u"#EXTINF:{0}\r\n".format(title)
                m3u += u"#EXTINF:%s,%s - %s\r\n" % (unicode(length), unicode(artist), unicode(title))
                

                if flat:
                    #m3u += s.path.filename
                    m3u += title
                else:
                    m3u += item

                m3u += u"\r\n"
            else:
                print "Ignoring. Item not found: %s" % item

        f.write(m3u)
        f.close()
        return m3u
        
