#!/usr/bin/env python
"""
# By: Charles Brandt [code at contextiskey dot com]
# On: *2012.09.19 17:50:21 
# License:  MIT

# Description:
helper functions, often needed in multiple modules

"""

import os, json, codecs, re
import logging
import subprocess
import zipfile

from moments.path import Path
from moments.journal import Journal

def save_json(destination, json_objects):
    json_file = codecs.open(destination, 'w', encoding='utf-8', errors='ignore')
    json_file.write(json.dumps(json_objects))
    json_file.close()    

def load_json(source_file, create=False):
    if not os.path.exists(source_file):
        json_objects = {}
        if create:
            print "CREATING NEW JSON FILE: %s" % source_file
            json_file = codecs.open(source_file, 'w', encoding='utf-8', errors='ignore')
            #make sure there is something there for subsequent loads
            json_file.write(json.dumps(json_objects))
            json_file.close()
        else:
            raise ValueError, "JSON file does not exist: %s" % source_file
    else:
        json_file = codecs.open(source_file, 'r', encoding='utf-8', errors='ignore')

        try:
            json_objects = json.loads(json_file.read())
        except:
            raise ValueError, "No JSON object could be decoded from: %s" % source_file
        json_file.close()
    return json_objects

def find_htmls(item):
    p = Path(item)
    if p.type() == "Directory":
        root = item
    else:
        parent = p.parent()
        root = str(parent)

    matches = []
    options = os.listdir(root)
    for o in options:
        if re.search('.*\.html$', o):
            html = os.path.join(root, o)
            matches.append(html)
            
    return matches
    
def find_zips(item):
    p = Path(item)
    if p.type() == "Directory":
        root = item
    else:
        parent = p.parent()
        root = str(parent)

    matches = []
    options = os.listdir(root)
    for o in options:
        if re.search('.*\.zip$', o):
            zipf = os.path.join(root, o)
            matches.append(zipf)
            
    return matches
    
def make_json_path(item):

    name = ''
    parent = ''

    p = Path(item)
    if p.type() == "Directory":
        #item must be a directory... just look here
        parent = p
        name = p.name
    else:
        name = p.name
        #must be some other file type... load the parent directory:
        parent = p.parent()

    json_name = "%s.json" % name
    print json_name
    return os.path.join(unicode(parent), json_name)

def find_json(item, limit_by_name=True, debug=False):
    """
    take any string
    see if it is a path for a json file
    or a path to a directory that contains a json file
    or look in the same directory as the item

    if more than one json file found, print a warning
    return the last json file

    if limit_by_name is true, and if item is a (non-json) file,
    use its filename to limit jsons to match that filename by default
    """
    if re.search('.*\.json$', item):
        if debug:
            #print "find_and_load_json: item is a json string: %s" % item
            logging.debug("find_json: item is a json string: %s" % item)
        return item

    else:
        parent = ''
        name = ''
        p = Path(item)
        if p.type() == "Directory":
            #item must be a directory... just look here
            parent = p
            d = p.load()
        else:
            name = p.name
            #must be some other file type... load the parent directory:
            parent = p.parent()
            d = parent.load()
            if debug:
                print "%s not a directory, using: %s" % (item, parent)
            
        matches = []
        for j in d.files:
            #if debug:
            #    print "Checking: %s" % j
            if re.search('\.json$', unicode(j)):
                if debug:
                    print "matched json: %s" % j

                match = os.path.join(unicode(parent), unicode(j))
                #this should allow us to hone in on one
                #if there is more than one media file in a directory
                if name and limit_by_name:
                    if re.search(name, unicode(j)):
                        matches.append(match)
                    else:
                        if debug:
                            print "could not find %s in %s" % (name, unicode(j))
                else:
                    matches.append(match)

        if debug:
            print "Found the following: %s" % matches

        if not matches:
            return None
        elif len(matches) == 1:
            logging.debug("find_json: found match: %s" % matches[0])
            return matches[0]
        else:
            #found more than one
            logging.debug("find_json: found many: %s" % matches)
            print "WARNING: find_json: more than one match found: %s" % matches

            logging.debug("find_json: returning last: %s" % matches[-1])

            return matches[-1]


def get_media_dimensions(movie_p, debug=False):
    """
    expects a full path to a media item
    use ffmpeg to query media for dimensions
    return a string representation of the size

    sudo apt-get install libav-tools
    """
    #command1 = "ffmpeg -i %s" % (movie_p)
    command1 = "avconv -i %s" % (movie_p)
    #print command1
    process = subprocess.Popen(command1, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    #output = process.communicate()[0]
    output = process.communicate()[1]

    #print output
    size = None
    lines = output.splitlines()
    for line in lines:
        #print line
        if re.search('Stream', line):
            if re.search('Video', line):
                #this is specific to the version of ffmpeg you are using
                #adjust accordingly
                parts = line.split(' ')
                if debug:
                    print "FOUND: %s" % parts
                #size = parts[-1]
                for p in parts:
                    if re.search('x', p) and len(p.split('x')) == 2:
                        size = p

                #get rid of trailing commas:
                if re.search(',$', size):
                    size = size[:-1]
                    
                #size = parts[-11]

    #print size
    return size

def get_media_properties(movie_p, debug=False):
    """
    expects a full path to a media item
    use ffmpeg/avconv to query media for dimensions

    return a string representation of the size
    the duration in seconds
    and the file size

    sudo apt-get install libav-tools
    """
    #command1 = "ffmpeg -i %s" % (movie_p)
    command1 = 'avconv -i "%s"' % (movie_p)
    #print command1
    process = subprocess.Popen(command1, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    #output = process.communicate()[0]
    output = process.communicate()[1]

    #print output
    size = None
    seconds = None
    
    lines = output.splitlines()
    for line in lines:
        #print line
        if re.search('Stream', line):
            if re.search('Video', line):
                #this is specific to the version of ffmpeg you are using
                #adjust accordingly
                parts = line.split(' ')
                if debug:
                    print "FOUND: %s" % parts
                #size = parts[-1]
                for p in parts:
                    if re.search('x', p) and len(p.split('x')) == 2:
                        size = p

                #get rid of trailing commas:
                if re.search(',$', size):
                    size = size[:-1]
                    
                #size = parts[-11]
        elif re.search('Duration', line):
            #print "DURATION!!"
            #print line
            parts = line.split()
            #print parts
            dstring = parts[1].replace(',', '')
            #print dstring
            h, m, s = dstring.split(':')
            seconds = (int(h) * 60 * 60) + (int(m) * 60) + float(s)
            #print seconds
        else:
            #could look for other content here:
            #print line
            pass

    if not seconds:
        print "\n\n"
        print "Warning! Could not parse output from avconv!!"
        print "Media file probably corrupt"
        print lines

        #optional to raise an error here:
        #raise ValueError, "Invalid media. See above output"
        
    #could return filesize if needed (content.update_dimensions handles this)
    #filesize = os.path.getsize(movie_p)

    #print size
    return size, seconds

def grab_frame(movie_p, position, destination=None, debug=False):
    """
    expects a full path to a media item
    use ffmpeg/avconv to extract a frame from the specified file

    position is in seconds
    
    sudo apt-get install libav-tools

    http://blog.roberthallam.org/2010/06/extract-a-single-image-from-a-video-using-ffmpeg/comment-page-1/
    http://ubuntuforums.org/showthread.php?t=2014630
    """
    if not destination:
        parent = os.path.dirname(movie_p)
        destination = os.path.join(parent, '1.jpg')
        
    #command1 = "ffmpeg -i %s" % (movie_p)
    command1 = "avconv -i %s" % (movie_p)
    #command1 = "ffmpeg -ss %s -i %s -t 1 -s 480x300 -f image2 imagefile.jpg" % (position, movie_p)
    #command1 = "avconv -ss %s -i %s -t 1 -f image2 1.jpg" % (position, movie_p)
    command1 = "avconv -ss %s -i %s -t 1 -f image2 %s" % (position, movie_p, destination)
    #print command1
    process = subprocess.Popen(command1, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    #output = process.communicate()[0]
    output = process.communicate()[1]

    return destination

def extract_zip(zip_file, debug=False):
    """
    >>> a = 'hello'
    >>> os.path.split(a)
    ('', 'hello')
    """
    
    sources = []
    zipp = Path(zip_file)
    #print zipp.name
    #zip_root = os.path.join(content.path, zipp.name)
    zip_root = os.path.join(os.path.dirname(zip_file), zipp.name)
    #sources.append(zip_root)
    if not os.path.exists(zip_root):
        os.makedirs(zip_root)
        
    zfile = zipfile.ZipFile(zip_file)
    for name in zfile.namelist():
        (dirname, filename) = os.path.split(name)
        #print "Decompressing " + filename + " on " + dirname
        dest_dir = os.path.join(zip_root, dirname)
        if not dest_dir in sources:
            sources.append(dest_dir)
        if debug:
            print "Decompressing " + filename + " to " + dest_dir + "<br>"
        if not os.path.exists(dest_dir):
             os.makedirs(dest_dir)

        dest = os.path.join(dest_dir, name)
        if not os.path.exists(dest):
            fd = open(dest, "w")
            fd.write(zfile.read(name))
            fd.close()
            #dpath = Path(dest)
            #print "making thumb"
            #img = dpath.load()
            #img.make_thumbs(['small'], save_original=False)

    return sources

def load_cloud(cloud_name, cloud_file):
    if not cloud_file:
        raise ValueError, "No cloud_file supplied: %s" % cloud_file

    if not os.path.exists(cloud_file):
        raise ValueError, "Couldn't find cloud file: %s" % cloud_file
    
    clouds = Journal(cloud_file)

    if clouds:
        if clouds.tag(cloud_name):
            cur_cloud = clouds.tags(cloud_name)[0].data.split()
        else:
            cur_cloud = []
            print "no clouds found for tag: %s in %s" % (cloud_name, cloud_file)
    return cur_cloud



def find_and_load_json(item, debug=False):
    """
    look in the same directory as item for a json file
    if found, load it and return the loaded object
    otherwise return None

    also [2013.07.03 10:30:19]
    deprecated:
    probably better to find_json()
    then load_json()
    """
    if re.search('.*\.json', item):
        if debug:
            #print "find_and_load_json: item is a json string: %s" % item
            logging.debug("find_and_load_json: item is a json string: %s" % item)
        loaded = load_json(item)
    else:
        p = Path(item)
        if p.type() == "Directory":
            parent = p
            d = p.load()
        else:
            parent = p.parent()
            d = parent.load()
            
        loaded = None
        for j in d.files:
            if re.search('.*\.json', str(j)):
                logging.debug("find_and_load_json: loading from: %s" % j)
                #print "find_and_load_json: loading from: %s" % j

                match = os.path.join(str(parent), str(j))
                loaded = load_json(match)
                #jso = file(os.path.join(str(parent), str(j)))
                #loaded = json.loads(jso.read())
                
    return loaded

