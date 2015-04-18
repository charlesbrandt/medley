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

import sys, os, re
import subprocess

from medley.helpers import load_json, save_json
from medley.content import Content
from medley.playlist import Playlist
from medley.formats import M3U

def usage():
    print __doc__

def copy_file(source, destination, verbose=False):
    """
    copy a single file 
    """
    #if not destination:
    if os.path.exists(destination):
        print "skipping: %s" % destination
        pass
    else:
        dest_path = os.path.dirname(destination)
        if not dest_path:
            dest_path = os.path.abspath('./')
            print "USING PATH: %s" % dest_path
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        #cp = subprocess.Popen("cp %s %s" % (source, destination), shell=True, stdout=subprocess.PIPE)
        #cp.wait()
        command = 'rsync -av "%s" "%s"' % (source, destination)
        rsync = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if verbose:
            print command
            print rsync.communicate()[0]
        else:
            rsync.communicate()[0]
                
def copy_media(source, destination=''):
    if os.path.exists(source):
        pl = None
        if re.search('m3u$', source):
            #load it as an M3U:
            print "LOADING AS M3U: %s" % source
            pl = M3U(source)
        else:
            pl = Playlist()
            pl.load(source)

        if not os.path.exists(destination):
            os.makedirs(destination)        
            
        for content in pl:
            path = os.path.join(content.path, content.filename)
            print path
            if content != content.root:
                #parent_path = os.path.join(content.parent.path, content.parent.filename)
                #print parent_path
                print "Extracting segment from parent content"
                content.extract_segment(destination)
            else:
                print "only need to copy original path"
                this_dest = os.path.join(destination, content.filename)
                copy_file(path, this_dest)
                
            #print content.debug()
        print pl
    else:
        print "Couldn't find path: %s" % source
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
            print "OUTPUT TO TEMP!"
            destination = './temp'

    copy_media(source, destination)

    if destination == './temp':
        print 
        print "OUTPUT TO TEMP!!"

## from moments.journal import Journal
## from moments.path import load_journal, Path, check_ignore
## #from medialist.medialist import MediaList
## #from medley.sources import Converter, Sources, Source
## from medley.formats import Converter

## def flatten_structure(source, destination):
##     """
##     copy all files that match check (e.g. mp3 files)
##     to a single directory
##     removing all other directory structures
##     does not need a playlist
##     only a source directory
##     """
##     ignore_dirs = [ 'downloads' ]
##     all_audio = []
##     mp3_check = re.compile('.*\.mp3$')
##     if os.path.isdir(source):
##         for root,dirs,files in os.walk(source):
##             for f in files:
##                 if not mp3_check.search(f):
##                     #didn't match our criteria... moving on
##                     continue

##                 if not check_ignore(os.path.join(root, f), ignore_dirs):
##                     #if we get here, it must match the check,
##                     #and is not in the ignore
##                     all_audio.append(os.path.join(root, f))

##     elif os.path.isfile(source) and mp3_check.search(source):
##         all_audio.append(source)

##     print "found the following audio files in path: %s" % source
##     print all_audio
##     for f in all_audio:
##         f_path = Path(f)
##         f_name = f_path.filename
##         f_dest = os.path.join(destination, f_name)
##         print "copying: %s to %s" % (f, f_dest)
##         copy_file(f, f_dest)
    
## def flatten():
##     source = sys.argv[1]
##     #destination = '/binaries/music/vinyl/flat/'
##     destination = './flat'
    
## def make_destination(source, translate):
##     if translate is not None:
##         (pre, post) = translate.split(':')
##     else:
##         (pre, post) = ('/c/media', '')

##     print "source: %s" % source
##     source = str(source)
##     destination = source.replace(pre, post)
##     #print "destination: %s" % destination
    
##     #change the path used in logs to your local path
##     #in this case, just remove the prefix /c/media
##     #destination = source.replace('/c/media', '')

    
##     #or can hard code it here (would flatten out everything sent)
##     #destination = '/c/media/binaries/graphics/dwt/20090405-telepaths_show/shared/'
##     source = Path(source)
##     destination = source.filename

##     #filename = os.path.basename(source)
##     #destination = '/c/trial/off/' + filename
    
##     return destination

## def copy_file(source, destination, verbose=False):
##     """
##     copy a single file 
##     """
##     #if not destination:
##     if os.path.exists(destination):
##         print "skipping: %s" % destination
##         pass
##     else:
##         dest_path = os.path.dirname(destination)
##         if not dest_path:
##             dest_path = os.path.abspath('./')
##             print "USING PATH: %s" % dest_path
##         if not os.path.exists(dest_path):
##             os.makedirs(dest_path)

##         #cp = subprocess.Popen("cp %s %s" % (source, destination), shell=True, stdout=subprocess.PIPE)
##         #cp.wait()
##         command = 'rsync -av "%s" "%s"' % (source, destination)
##         rsync = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
##         if verbose:
##             print command
##             print rsync.communicate()[0]
##         else:
##             rsync.communicate()[0]
            
## def process_files(source_list, translate=None, action="copy", m3u_dest="temp.txt"):
##     """
##     copy *only* the files referenced in a source_list to a new loacation
##     """
##     result = ''
    
##     #j = Journal()
##     #j.from_file(journal)
##     #j = load_journal(journal)
##     #m = MediaList()
##     #m.from_journal(j, local_path='/c')
##     #sources = Sources()

##     sl = Path(source_list)
##     assert sl.exists()
##     converter = Converter()

##     if sl.extension == ".m3u":
##         print "M3U!"
##         sources = converter.from_m3u(source_list)
##     elif sl.extension == ".txt":
##         sources = converter.from_journal(source_list)
##     else:
##         print "UNKNOWN EXTENSION: %s" % sl.extension

    
##     new_sources = Sources()
##     counter = 0
##     for i in sources:
##         #print i
##         #if re.search('\.mp3', i.path):
##         if os.path.exists(str(i.path)):
##             destination = make_destination(i.path, translate)
##             #print "SOURCE: %s" % i
##             print "DEST: %s" % destination

##             if action == "copy":
##                 print "Copy %03d: %s" % (counter, i.path)
##                 copy_file(i.path, destination)
##             if action == "m3u":
##                 new_sources.append(Source(destination))
##         else:
##             print "COULD NOT FIND FILE: %s" % i.path
##         counter += 1

##     if action == "m3u":
##         #print len(new_sources)
##         m3u = converter.to_m3u(new_sources, verify=False)
##         #print m3u
##         print "SAVING M3U TO: %s" % m3u_dest
##         f = open(m3u_dest, 'w')
##         f.write(m3u)
##         f.close()
        
    
## def main():
##     if len (sys.argv) > 1:
##         if sys.argv[1] in ['--help','help', '-h', '--h', '-help']:
##             usage()
##         f1 = sys.argv[1]
##         translate = None
##         if len(sys.argv) > 2:
##             translate = sys.argv[2]


##         #for just a copy:
##         process_files(f1, translate)

##         #process_files(f1, translate, action="m3u")

## if __name__ == '__main__':
##     #see also:
##     #/c/medley/scripts/make_relative_playlist.py


##     main()
##     #flatten_structure(sys.argv[1], './flat2/')


