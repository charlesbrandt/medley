#!/usr/bin/env python
"""
#
# Description:
# originally based on copy_media.py
# updated to use JSON playlists pointing to Content objects...
# should use other scripts to help with that conversion as needed
#
# copy the refrenced files to a new directory
#


# By: Charles Brandt [code at charlesbrandt dot com]

# On: 2009.04.13 20:13:01 
# Also: 2009.07.25 10:23:48
# Also: 2015.03.19 18:36:23 
# License:  MIT



# Requires: medley, moments

"""
from __future__ import print_function

import sys, os, re
import subprocess

from medley.helpers import load_json, save_json
from medley.content import Content
from medley.playlist import Playlist
from medley.formats import M3U

def usage():
    print(__doc__)

def copy_file(source, destination, verbose=False):
    """
    copy a single file 
    """
    #if not destination:
    if os.path.exists(destination):
        print("skipping: %s" % destination)
        pass
    else:
        dest_path = os.path.dirname(destination)
        if not dest_path:
            dest_path = os.path.abspath('./')
            print("USING PATH: %s" % dest_path)
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        #cp = subprocess.Popen("cp %s %s" % (source, destination), shell=True, stdout=subprocess.PIPE)
        #cp.wait()
        command = 'rsync -av "%s" "%s"' % (source, destination)
        rsync = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if verbose:
            print(command)
            print(rsync.communicate()[0])
        else:
            rsync.communicate()[0]
                
def copy_media(source, destination=''):
    if os.path.exists(source):
        pl = None
        if re.search('m3u$', source):
            #load it as an M3U:
            print("LOADING AS M3U: %s" % source)
            pl = M3U(source)
        else:
            pl = Playlist()
            pl.load(source)

        if not os.path.exists(destination):
            os.makedirs(destination)        
            
        for content in pl:
            path = os.path.join(content.path, content.filename)
            print(path)
            if content != content.root:
                #parent_path = os.path.join(content.parent.path, content.parent.filename)
                #print parent_path
                print("Extracting segment from parent content")
                content.extract_segment(destination)
            else:
                print("only need to copy original path")
                this_dest = os.path.join(destination, content.filename)
                copy_file(path, this_dest)
                
            #print content.debug()
        print(pl)
    else:
        print("Couldn't find path: %s" % source)
        exit()
        
if __name__ == '__main__':
    source = None
    destination = None
    if len(sys.argv) > 1:
        helps = ['--help', 'help', '-h']
        for i in helps:
            if i in sys.argv:
                usage()
                exit()
        source = sys.argv[1]
        if len(sys.argv) > 2:
            destination = sys.argv[2]
        else:
            print("OUTPUT TO TEMP!")
            destination = './temp'

    copy_media(source, destination)

    if destination == './temp':
        print() 
        print("OUTPUT TO TEMP!!")

