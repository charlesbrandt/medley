#!/usr/bin/env python
"""
# By: Charles Brandt [code at contextiskey dot com]
# On: *2012.09.19 17:50:21 
# License:  MIT

# Description:
helper functions, often needed in multiple modules

"""
from __future__ import print_function
from builtins import str

import os, json, codecs, re
import logging
import subprocess
import zipfile

from moments.path import Path
from moments.journal import Journal
from moments.tag import to_tag

def save_json(destination, json_objects):
    json_file = codecs.open(destination, 'w', encoding='utf-8', errors='ignore')
    json_file.write(json.dumps(json_objects))
    json_file.close()    

def load_json(source_file, create=False):
    if not os.path.exists(source_file):
        json_objects = {}
        if create:
            print("CREATING NEW JSON FILE: %s" % source_file)
            json_file = codecs.open(source_file, 'w', encoding='utf-8', errors='ignore')
            #make sure there is something there for subsequent loads
            json_file.write(json.dumps(json_objects))
            json_file.close()
        else:
            raise ValueError("JSON file does not exist: %s" % source_file)
    else:
        json_file = codecs.open(source_file, 'r', encoding='utf-8', errors='ignore')

        try:
            json_objects = json.loads(json_file.read())
        except:
            raise ValueError("No JSON object could be decoded from: %s" % source_file)
        json_file.close()
    return json_objects

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

    #making jsons named as tags to help normalize difficult characters
    json_name = "%s.json" % to_tag(name)
    #print json_name
    return os.path.join(str(parent), json_name)

def find_jsons(item, limit_by_name=False, debug=False):
    """
    foundation for find_json
    but this returns all matches (based on parameters)
    """

    if re.search('.*\.json$', item):
        if debug:
            #print "find_and_load_json: item is a json string: %s" % item
            logging.debug("find_json: item is a json string: %s" % item)
        return [item]

    else:
        parent = ''
        name = ''
        p = Path(item)
        if p.type() == "Directory":
            #item must be a directory... just look here
            parent = p
            d = p.load()
        else:
            name = to_tag(p.name)
            #must be some other file type... load the parent directory:
            parent = p.parent()
            d = parent.load()
            if debug:
                print("%s not a directory, using: %s" % (item, parent))
            
        matches = []
        for j in d.files:
            #if debug:
            #    print "Checking: %s" % j
            if re.search('\.json$', str(j)):
                if debug:
                    print("matched json: %s" % j)

                match = os.path.join(str(parent), str(j))
                #this should allow us to hone in on one
                #if there is more than one media file in a directory
                if name and limit_by_name:
                    if re.search(name, str(j)):
                        matches.append(match)
                    else:
                        if debug:
                            print("could not find %s in %s" % (name, str(j)))
                else:
                    matches.append(match)

        if debug:
            print("Found the following: %s" % matches)

        return matches
    
def find_json(item, limit_by_name=False, debug=False):
    """
    take any string
    see if it is a path for a json file
    or a path to a directory that contains a json file
    or look in the same directory as the item

    if more than one json file found, print a warning
    return the last json file

    if limit_by_name is true, and if item is a (non-json) file,
    use its filename to limit jsons to match that filename by default
    also [2016.04.10 14:21:49]
    switching this behavior
    now if limit_by_name is set to true,
    it will only return a result if the name matches
    otherwise the default behavior will be to try to match the name
    if there is more than one json in the directory
    otherwise it won't be strict
    
    """
    matches = find_jsons(item, limit_by_name, debug)

    if not matches:
        return None

    elif len(matches) == 1:
        logging.debug("find_json: found match: %s" % matches[0])
        return matches[0]

    else:
        #found more than one
        logging.debug("find_json: found many: %s" % matches)

        #even if limit by name was not specified as true,
        #in the case of multiple matches,
        #it may still make sense to try to match by name
        #if no match, then it's still possible to return the last one
        found = False
        name = ''
        p = Path(item)
        #maybe this should be checked for directories too???
        if p.type() != "Directory":
            name = to_tag(p.name)
            
        if name: 
            for match in matches:
                if re.search(name, str(match)):
                    found = match

        if found:
            logging.debug("find_json: matched name: %s" % found)
            return found
        else:
            print("WARNING: find_json: more than one match found: %s" % matches)
            logging.debug("find_json: returning last: %s" % matches[-1])
            return matches[-1]


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

def find_media(item):
    """
    using this in content.import_content to check for time based media
    (videos or sounds)
    """
    p = Path(item)
    if p.type() == "Directory":
        root = p.load()
    else:
        parent = p.parent()
        root = parent.load()

    matches = []
    #now root is a directory...
    #use that to help find media
    root.scan_filetypes()
    matches.extend(root.sounds)
    matches.extend(root.movies)
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
                    print("FOUND: %s" % parts)
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

    return a string representation of the dimensions (size) (not file size)
    the duration in seconds
    and the bitrate

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
    dimensions = None
    seconds = None
    bitrate = None
    
    lines = output.splitlines()
    for line in lines:
        #print line
        if re.search('Stream', line):
            if re.search('Video', line):
                #this is specific to the version of ffmpeg you are using
                #adjust accordingly
                parts = line.split(' ')
                if debug:
                    print("FOUND: %s" % parts)
                #dimensions = parts[-1]
                for p in parts:
                    if re.search('x', p) and len(p.split('x')) == 2:
                        dimensions = p

                #get rid of trailing commas:
                if re.search(',$', dimensions):
                    dimensions = dimensions[:-1]
                    
                #dimensions = parts[-11]
        elif re.search('Duration', line):
            #print "DURATION!!"
            #print line
            parts = line.split()
            #print parts
            dstring = parts[1].replace(',', '')
            #print dstring
            h, m, s = dstring.split(':')
            seconds = (int(h) * 60 * 60) + (int(m) * 60) + float(s)
            bitrate = parts[5]
            #print seconds
        else:
            #could look for other content here:
            #print line
            pass

    if not seconds:
        print("\n\n")
        print("Warning! Could not parse output from avconv!!")
        print("Media file probably corrupt")
        for line in lines:
            print(line)

        #optional to raise an error here:
        #raise ValueError, "Invalid media. See above output"
        
    #could return filesize if needed (content.update_dimensions handles this)
    #filesize = os.path.getsize(movie_p)

    #print dimensions
    return dimensions, seconds, bitrate

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
    #command1 = "avconv -i %s" % (movie_p)
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
            print("Decompressing " + filename + " to " + dest_dir + "<br>")
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
        raise ValueError("No cloud_file supplied: %s" % cloud_file)

    if not os.path.exists(cloud_file):
        raise ValueError("Couldn't find cloud file: %s" % cloud_file)
    
    clouds = Journal(cloud_file)

    if clouds:
        if clouds.tag(cloud_name):
            cur_cloud = clouds.tags(cloud_name)[0].data.split()
        else:
            cur_cloud = []
            print("no clouds found for tag: %s in %s" % (cloud_name, cloud_file))
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


