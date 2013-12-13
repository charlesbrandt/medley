#!/usr/bin/env python
"""
*2012.03.27 10:56:06 
this is really a media database front end, which at one time was jumbled up with Pose, but it really should be separate...
this does not have the focus on moments

*2012.03.25 19:54:37 
consider the boundary between this and Pose...
Pose seems to have developed into more of a Journal viewer application...

this should bring back some of the earlier functionality of viewing galleries of images, etc...
not necessarily tied to Moments...
more of a movie / media database front end.

*2012.09.19 17:41:02 
launch by running:
python application.py /path/to/collection/root/



*2013.05.17 15:17:53
SEE ALSO:
python /c/mindstream/mindstream/launch.py -c /c/alpha/music_manager todo

python /c/mindstream/mindstream/launch.py -c /c/trees todo


"""
import logging, re

from bottle import static_file
from bottle import get, post, request
from bottle import route, run
from bottle import template

#DO NOT USE THIS IN PRODUCTION!!
import bottle
bottle.debug(True)

import os
server_root = os.path.dirname(os.path.realpath(__file__))
#default is "./views/" directory
template_path = os.path.join(server_root, 'templates')
bottle.TEMPLATE_PATH.append(template_path)

import sys, codecs, json

from helpers import load_json, find_zips
from collector import Collections, Collection, CollectionSummary
from people import People

from moments.path import Path

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(filename="debug.log", level=logging.DEBUG)


#from moments.tag import to_tag
#from moments.timestamp import Timestamp

#from mmdb import Collection, Scene, load_collections, get_collection, Scenes, save_groups, load_cloud, Star
#from sort_media import group_by_type
#from cloud_merge import merge_simple

#this will get loaded in launch...
#making it global
configs = {}

def usage():
    print __doc__
    
@route('/robots.txt')
def robots_static():
    path = os.path.join(server_root)
    return static_file("robots.txt", root=path)
  
@route('/humans.txt')
def humans_static():
    path = os.path.join(server_root)
    return static_file("humans.txt", root=path)
  
@route('/apple-touch-icon:suffix#.+#')
def apple_touch_static(suffix):
    path = os.path.join(server_root)
    filename = "apple-touch-icon%s" % suffix
    return static_file(filename, root=path)

@route('/css/:filename#.+#')
def css_static(filename):
    css_path = os.path.join(server_root, 'css')
    return static_file(filename, root=css_path)

@route('/js/:filename#.+#')
def js_static(filename):
    js_path = os.path.join(server_root, 'js')
    return static_file(filename, root=js_path)

@route('/img/:filename#.+#')
def images_static(filename):
    image_path = os.path.join(server_root, 'img')
    return static_file(filename, root=image_path)
  
#to force a download, use the following:
#    return static_file(filename, root='/path/to/static/files', download=filename)

@route('/help')
def help():
    return template('help')

path_root = "/"

@route('/path/:relative#.+#')
def path(relative=''):
    """
    serve a static file

    this also allows pose to function as a customizable file system browser

    be careful with what you set path_root to
    if the machine you run this on has sensitive information
    and is connected to a public network
    """
    global path_root

    if re.match('~', relative):
        relative = os.path.expanduser(relative)

    full_path = os.path.join(path_root, relative)
 
    path = Path(full_path, relative_prefix=path_root)
    if path.type() == "Directory":
        #we shouldn't be returning directory listing here
        pass    
    else:
        #this is equivalent to a view...
        #indicate it in the log:
        #path.log_action()
        return static_file(relative, root=path_root)



def get_summary(collection_name):
    """
    helper to look through local config list of collections
    find the right path
    add it to config['root']
    then load the collection

    this needs to be done local to the application
    since it will have all of the configuration details
    """
    collections = Collections(configs['root'], configs['collection_list'])
    collections.load_summaries()
    print "# of collection summaries loaded: %s" % len(collections)
    print "looking for: %s" % collection_name
    collection_summary = collections.get_summary(collection_name)
    return collection_summary
    
def get_collection(collection_name):
    collection_summary = get_summary(collection_name)
    print "COLLECTION SUMMARY ROOT: %s, META: %s" % (collection_summary.root, collection_summary.meta_root)
    collection = collection_summary.load_collection()
    return collection

    
@route('/rescan/:collection_name')
def rescan(collection_name=None):
    if collection_name:
        collection = get_collection(collection_name)
        summary = get_summary(collection_name)
        collection.summary = summary

        print "REPARSING COLLECTION: %s" % (collection_name)
        #don't think this is what we want here!!!
        #collection.reparse()
        summary.scan_metas()
        #summary.save()
    
    return template('rescan', collection=collection)

def people_path():
    path = configs['people_root']
    if re.match('^\.', path):
        path = os.path.join(configs['root'], path[2:])

    return path

def get_people():
    path = people_path()
    
    p = People(path, configs['person_term'])
    return p

@route('/person/:person_name')
def person(person_name):
    ppl = get_people()
    ppl.load()

    p_list = ppl.get(person_name)
    #print "Looked up: %s" % person_name
    #print "Received: %s" % p_list
    p = p_list[0]

    #in this case we want to remove person.tag from person.tags
    #so that tags only includes other tags
    p.tags.remove(p.tag)


    related = ppl.search(person_name)

    #check for available content here (or meta data for content)
    p.load_content()

    collections = Collections(configs['root'], configs['collection_list'])
    #this should be redundant:
    #collections.load_summaries()


    #locate a default image
    path = people_path()
    for content in p.contents:
        #logging.info(path)
        
        #this method works for finding images,
        #but trying to be consistent if possible:
        ## #logging.info(os.path.join(path, content.base_dir))
        ## full_path = os.path.join(path, content.base_dir)
        ## bdp = Path(full_path)
        ## directory = bdp.load()
        ## directory.scan_filetypes()
        ## #logging.info(directory.images)
        ## if directory.images:
        ##     #get rid of leading slash:
        ##     content.image = directory.images[0].path[1:]
        ##     #logging.info(content.image)

        content.drive_dir = path
        images = content.find_media(kind="Image", relative=False, debug=True)
        if images:
            print images
            content.image = images[0]

        else:
            content.image = ''

        #check if content's collection is available
        collection_name = content.remainder['collection']
        collection_summary = collections.get_summary(collection_name)
        #collection = collection_summary.load_collection()

        #logging.info("%s available? %s" % (collection_name, collection_summary.available))

        if len(collection_summary.available):
            content.available = True
        else:
            content.available = False

            
    #TODO:
    #default external links (search concerts, etc)
    #these should be configured based on collection (not hard coded here)
    
    #TODO:
    #track history / notes (manual journal ok)

    return template('person', person=p, related=related)

@route('/people')
def people():
    print configs
    print configs['people_root']
    print configs['person_term']

    p = get_people()
    
    #cs = CollectionSummary(path)
    #print cs.summary()

    #cluster = cs.load_cluster()
    #print cluster
        
    #return template('collection', summary=summary, c=collection, cluster=cluster)
 
    #collections = load_collections(collection_root)
    #collections = Collections(, configs['collection_list'])
    #print len(collections)
    #return template('people', collections=collections)
    return template('people', summary=people, cluster=p.cluster)

@route('/collection/:collection_name/zip/:content_name#.+#')
def collection_zip(collection_name=None, content_name=None):
    """

    """
    result = ''
    content = None
    if collection_name:
        summary = get_summary(collection_name)
        content = summary.load_content(content_name)
        if content:

            sources = []
            content.zips = find_zips(content.path)
            import zipfile
            for zipf in content.zips:
                zipp = Path(zipf)
                #print zipp.name
                zip_root = os.path.join(content.path, zipp.name)
                if not os.path.exists(zip_root):
                    os.makedirs(zip_root)
                zfile = zipfile.ZipFile(zipf)
                for name in zfile.namelist():
                    (dirname, filename) = os.path.split(name)
                    #print "Decompressing " + filename + " on " + dirname
                    dest_dir = os.path.join(zip_root, dirname)
                    if not dest_dir in sources:
                        sources.append(dest_dir)
                    print "Decompressing " + filename + " to " + dest_dir + "<br>"
                    if not os.path.exists(dest_dir):
                         os.makedirs(dest_dir)
                    dest = os.path.join(dest_dir, name)
                    if not os.path.exists(dest):
                        fd = open(dest, "w")
                        fd.write(zfile.read(name))
                        fd.close()
                        dpath = Path(dest)
                        print "making thumb"
                        img = dpath.load()
                        img.make_thumbs(['small'], save_original=False)


            zips = []
            for source in sources:
                spath = Path(source, relative_prefix=path_root)
                sdir = spath.load()
                zips.append(sdir.contents)
                print source

    #return template('simple', body=result, title="unzip!")
    return template('zip', zips=zips)
  
@route('/collection/:collection_name/content/:content_name#.+#')
def collection_content(collection_name=None, content_name=None):
    content = None
    if collection_name:
        summary = get_summary(collection_name)
        content = summary.load_content(content_name)
        if content:
            images = content.find_media(kind="Image", relative=False, debug=True)
            if images:
                #print images
                content.image = images[0]
            else:
                content.image = None
                
            content.movies = content.find_media(relative=False, debug=True)
            content.sounds = content.find_media(kind="Sound", relative=False, debug=True)
            content.zips = find_zips(content.path)
            print content.zips
            print content_name, content.base_dir
            return template('content', content=content, collection=collection_name)

    message = "Could not find: %s in %s" % (content_name, collection_name)
    return template('404', message=message)

@route('/collection/:collection_name/person/:person_name')
def collection_person(collection_name=None, person_name=None):
    if collection_name:
        summary = get_summary(collection_name)
        #print summary
        #needed for current podcasts rendering approach:
        #summary.load_scraper()

        collection = get_collection(collection_name)
        #print collection

        #drive_root = os.path.dirname(os.path.dirname(summary.available[0]))
        drive_root = os.path.dirname(summary.available[0])
        print drive_root

        #filter the whole collection down to only items with this person:
        results = []
        for content in collection:
            if person_name in content.people:
                #print "MATCH!"
                #print content
                results.append(content)
                if len(summary.available):
                    content.cur_path = os.path.join(drive_root, content.base_dir)
                    content.options = os.listdir(content.cur_path)
                    content.image = ''
                    for option in content.options:
                        if re.search("sample.jpg", option):
                            content.image = os.path.join(content.cur_path, option)
                        
    else:
        summary = None
        results = []
        collection = None

    return template('collection_person', name=person_name, summary=summary, c=collection, results=results)
        

        
@route('/collection/:collection_name')
def collection(collection_name=None):
    if collection_name:
        summary = get_summary(collection_name)
        print summary
        #needed for current podcasts rendering approach:
        #summary.load_scraper()

        collection = get_collection(collection_name)
        print collection
        print "APP load_cluster()"
        cluster = summary.load_cluster()
        print cluster
        
    else:
        summary = None

    return template('collection', summary=summary, c=collection, cluster=cluster)
        

@route('/collections')
def collections_details():
    #collections = load_collections(collection_root)
    collections = Collections(configs['root'], configs['collection_list'])
    #print len(collections)
    return template('collections', collections=collections)

@route('/')
def index():
    #collections = load_collections(collection_root)
    collections = Collections(configs['root'], configs['collection_list'])
    #print len(collections)
    return template('main', collections=collections)



def launch():
    global configs
    
    #one argument must be passed in for root
    if len(sys.argv) > 1:
        helps = ['--help', 'help', '-h']
        for i in helps:
            if i in sys.argv:
                usage()
                exit()
        root = sys.argv[1]
        config_json = os.path.join(root, "config.json")
        try:
            configs = load_json(config_json)
        except:
            #set up a default config here:
            configs = { 'collection_list': [ './beats_in_space/' ],
                        #listing collections seems easier
                        #than a specific path where they all must be:
                        #collection_root: './collections',
                        'people_root': './artists/',
                        #could be star, musician, user, preson, etc:
                        'person_term': 'artist',
                        'group_root': None,
                        #could be band, team, etc
                        'group_term': 'group',
                        'use_group': True,
                        'cloud_file': './clouds.txt',
                        'cloud_contents': 'artists',
                        'categories': [ 'sleep', 'work', 'chill', 'meditate', 'love', 'other', 'captain', 'pop' ],
                        'host': 'localhost',
                        'port': '8080',
                        }

            print "CREATING NEW CONFIG FILE: %s" % config_json
            json_file = codecs.open(config_json, 'w', encoding='utf-8', errors='ignore')
            json_file.write(json.dumps(configs))
            json_file.close()


        #add this in for global use:
        configs['root'] = root
        
        print configs
        #exit()
        #run(host='localhost', port=8080)
        run(host=configs['host'], port=configs['port'])

    else:
        usage()
        exit()
        
if __name__ == '__main__':
    launch()
