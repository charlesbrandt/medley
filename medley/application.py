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

from helpers import load_json
from collector import Collections, Collection, CollectionSummary
from people import People

logging.basicConfig(level=logging.DEBUG)



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
    collection.reparse()
    
    return template('rescan', collection=collection)

def get_people():
    path = configs['people_root']
    if re.match('^\.', path):
        path = os.path.join(configs['root'], path[2:])

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

    related = ppl.search(person_name)
    
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
