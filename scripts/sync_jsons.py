#!/usr/bin/env python
"""
# By: Charles Brandt [code at contextiskey dot com]
# On: 2014.07.09 14:56:09
# License:  MIT

# Requires: moments

# based off of:
# /c/templates/scripts/diff_directories.py

# Description:
#
# takes two directory paths as input
# looks at the contents of both directories
# and recursively finds json files with differences between the two of them

be very careful if merging automatically...
this is not a version control system.  more like copy contents of directories over one another and keeping the newer version.
potential for data loss there, but shouldn't be a big deal with one primary location.

few different approaches for the diff part:

1. read in json as actual object then compare that way:
http://stackoverflow.com/questions/11141644/how-to-compare-2-json-in-python

2. use dedicated library for the task:
https://pypi.python.org/pypi/json_tools
https://bitbucket.org/vadim_semenov/json_tools/src/75cc15381188c760badbd5b66aef9941a42c93fa?at=default
https://bitbucket.org/vadim_semenov/json_tools/wiki/Home

it employs json-patch:
http://tools.ietf.org/html/draft-ietf-appsawg-json-patch-02

3. diff textually:
http://stackoverflow.com/questions/4599456/textually-diffing-json

python diff_json_and_merge.py /path/to/d1 /path/to/d2

it is best if d1 is a subset of d2 (pruned collection derived from bigger one)

"""

# skelton for command line interaction:
import os, sys
import re
import subprocess, shutil
from datetime import datetime
import json, codecs

#http://docs.python.org/release/2.5.2/lib/module-difflib.html
from difflib import Differ, unified_diff
from pprint import pprint

from moments.path import Path
from moments.filters import unaccented_map

def usage():
    print __doc__

#from __future__ import print_function


def diff_json(local, other):
    """ Calculates the difference between two JSON documents.
        All resulting changes are relative to @a local.

        Returns diff formatted in form of extended JSON Patch (see IETF draft).

        via:
        https://bitbucket.org/vadim_semenov/json_tools/src/75cc15381188c760badbd5b66aef9941a42c93fa/lib/diff.py?at=default
    """

    def _recursive_diff(l, r, res, path='/'):
        if type(l) != type(r):
            res.append({
                'replace': path,
                'value': r,
                'details': 'type',
                'prev': l
            })
            return

        delim = '/' if path != '/' else ''

        if isinstance(l, dict):
            for k, v in l.iteritems():
                new_path = delim.join([path, k])
                if k not in r:
                    res.append({'remove': new_path, 'prev': v})
                else:
                    _recursive_diff(v, r[k], res, new_path)
            for k, v in r.iteritems():
                if k in l:
                    continue
                res.append({
                    'add': delim.join([path, k]),
                    'value': v
                })
        elif isinstance(l, list):
            ll = len(l)
            lr = len(r)
            if ll > lr:
                for i, item in enumerate(l[lr:], start=lr):
                    res.append({
                        'remove': delim.join([path, str(i)]),
                        'prev': item,
                        'details': 'array-item'
                    })
            elif lr > ll:
                for i, item in enumerate(r[ll:], start=ll):
                    res.append({
                        'add': delim.join([path, str(i)]),
                        'value': item,
                        'details': 'array-item'
                    })
            minl = min(ll, lr)
            if minl > 0:
                for i, item in enumerate(l[:minl]):
                    _recursive_diff(item, r[i], res, delim.join([path, str(i)]))
        else:  # both items are atomic
            if l != r:
                res.append({
                    'replace': path,
                    'value': r,
                    'prev': l
                })
    

    result = []
    _recursive_diff(local, other, result)
    return result

def print_reduced(diff, pretty=True):
    """ Prints JSON diff in reduced format (similar to plain diffs).
    """
    print diff
    for action in diff:
        if 'add' in action:
            print '+', action['add'], action['value']
        elif 'remove' in action:
            print '-', action['remove'], action['prev']



def diff_system(path1, path2):
    #this will show differences if cases are different:
    #i.e. MUSIC != Music
    #case sensitive:

    diff = subprocess.Popen(["diff", path1, path2], stdout=subprocess.PIPE).communicate()[0]
    print "DIFF OUTPUT:"
    print diff

def load_json(source_file):
    if not os.path.exists(source_file):
        json_objects = {}
    else:
        json_file = codecs.open(source_file, 'r', encoding='utf-8', errors='ignore')

        try:
            json_objects = json.loads(json_file.read())
        except:
            raise ValueError, "No JSON object could be decoded from: %s" % source_file
        json_file.close()
    return json_objects

def diff_files(fname, path1, path2, indent, sync=False, use_system_diff=False):

    #until we prove otherwise, we'll assume they're different
    is_difference = True
    added = False
    skipped = False
    
    p1 = Path(path1)
    n1 = p1.load()
    n1.check_size()

    p2 = Path(path2)
    n2 = p2.load()
    n2.check_size()

    if n1.size == n2.size:
        #probably pretty safe to assume that they are equal
        #print " %s - BOTH, SAME SIZE" % phraseUnicode2ASCII(fname)
        is_difference = False

        #could do additional checks if desired
        #enabling another diff level will take longer, but will be more accurate:
        f_a = file(path1)
        f_b = file(path2)
        a = f_a.readlines()
        b = f_b.readlines()
        diff = unified_diff(a, b)
        for d in diff:
            is_difference = True
            #print d

        #this will signal which files have differences:
        if is_difference:
            print "EQUAL sizes: %s %s" % (n1.size, n2.size)
            print " %s - BOTH, DIFFERENT CONTENT" % fname.translate(unaccented_map())

            print "Exiting...  should investigate difference further"
            #this is not a common situation... should check what is going on
            exit()
            
        #could move it somewhere else:
        #os.rename(path1, os.path.join(d1, "dupes", fname))
        #os.rename(path2, os.path.join(d2, "merged", fname))

    else:
        print "%s - BOTH, DIFFERENT SIZE" % fname.translate(unaccented_map())
        print "sizes: %s %s" % (n1.size, n2.size)

        n1.check_stats()
        n2.check_stats()
        print n1.mtime
        print n2.mtime

        #if n1 is bigger size and newer, should be ok to copy it over to n2
        if (n1.size > n2.size) and (n1.mtime > n2.mtime):
            print "N1 is bigger and newer."

            result = diff_json(path2, path1)
            print_reduced(result)

            import jsonpatch
            src = load_json(path2)
            dst = load_json(path1)
            patch = jsonpatch.make_patch(src, dst)
            print patch

            if sync:
                print "cp %s %s" % (path1, path2)
                added = path1
                #WARNING! THIS DOES THE COPY... WILL OVERWRITE!!!!
                shutil.copy(path1, path2)

        elif (n1.size < n2.size) and (n1.mtime > n2.mtime):
            print "N1 is smaller but newer.  Check what was removed..."
            #print "cp %s %s" % (path1, path2)

            #system diff doesn't help... json files often consist of one line:
            #diff_system( path1.translate(unaccented_map()),
            #             path2.translate(unaccented_map()) )

            
            #import jsonpatch
            #src = load_json(path1)
            #dst = load_json(path2)
            #patch = jsonpatch.make_patch(src, dst)
            #print patch

            result = diff_json(path2, path1)
            print_reduced(result)
            #print result
            skipped = path1

        elif (n1.size < n2.size) and (n1.mtime < n2.mtime):
            print "N2 is bigger and newer."

            result = diff_json(path1, path2)
            print_reduced(result)

            import jsonpatch
            src = load_json(path1)
            dst = load_json(path2)
            patch = jsonpatch.make_patch(src, dst)
            print patch

            print "cp %s %s" % (path2, path1)
            added = path2

            if sync:
                #WARNING! THIS DOES THE COPY... WILL OVERWRITE!!!!
                shutil.copy(path1, path2)

        
        if use_system_diff:
            print "diffing: %s %s\n" % (path1, path2)
            try:
                diff_system( path1.translate(unaccented_map()),
                             path2.translate(unaccented_map()) )
            except:
                print "Unable to diff."

    return (is_difference, added, skipped)



def diff_dirs(dpath1, dpath2, recurse=True, indent=0, show_both=False, sync=True ):
    
    is_difference = False
    skipped = []
    added = []

    p1 = Path(dpath1)
    d1 = p1.load()
    #d1 = make_node(dpath1, relative=False)
    d1.scan_directory()

    p2 = Path(dpath2)
    d2 = p2.load()
    #d2 = make_node(dpath2, relative=False)
    d2.scan_directory()
    d2contents = d2.listdir[:]
    
    for item in d1.listdir:
        #items to ignore:
        if (item not in [ "ignore_me.txt", ".hg" ]):

            #print datetime.now()
            n1path = os.path.join(dpath1, item)
            n2path = os.path.join(dpath2, item)

            if re.search('.*\.json$', item):

                if item in d2contents:
                    #they both have an item with the same name

                    d2contents.remove(item)
                    if show_both:
                        #print "%s - BOTH" % phraseUnicode2ASCII(i)
                        print "%s - BOTH" % item.translate(unaccented_map())

                    #TODO:
                    #do comparison and merge of json objects here:
                    (this_diff, this_added, this_skipped) = diff_files(item, n1path, n2path, indent, sync)
                    
                    is_difference |= this_diff
                    if this_diff:
                        print "For: %s" % n1path
                        #print "%s - DIFFERS" % item.translate(unaccented_map())
                        print ""

                    if this_added:
                        added.append(this_added)
                    if this_skipped:
                        skipped.append(this_skipped)

                else:
                    is_difference = True
                    print "%s - D1 ONLY" % item.translate(unaccented_map())
                    #could move it if desired:
                    #os.rename(n1path, n2path)

            else:

                #in this case, no need to compare... just remove
                if item in d2contents:
                    #they both have an item with the same name
                    d2contents.remove(item)
                    if show_both:
                        print "%s - BOTH" % item.translate(unaccented_map())
                
                p1 = Path(n1path)
                if p1.type() == "Directory":
                    if recurse:
                        (last_difference, last_added, last_skipped) = diff_dirs(n1path, n2path, recurse, indent+1, sync)
                        is_difference |= last_difference
                        added.extend(last_added)
                        skipped.extend(last_skipped)

                        ## if last_difference:
                        ##     print "Differences found: %s" % n1path
                        ##     #add a new line after finished with 
                        ##     if not indent:
                        ##         print "\n"
                    else:
                        print "No Comparison"


    #if anything is left in d2contents, it must not have been in d1
    if len(d2contents):
        is_difference = True
        #for item in d2contents:
        #    print "%s - D2 ONLY" % item.translate(unaccented_map())

    return is_difference, added, skipped

if __name__ == '__main__':
    if len (sys.argv) > 1:
        if sys.argv[1] in ['--help','help'] or len(sys.argv) < 2:
            usage()
        d1 = sys.argv[1]
        d2 = sys.argv[2]
        #go through each directory
        #look for matching .json files in both d1 and d2
        #if they're exactly the same, skip
        #if they're the same filename, but different contents:
        #   - check which one has newer content (timestamp)
        #        - if newer is larger, use it
        #        - if newer is smaller, show visual diff (or an alert at minimum)

        #debug mode to show what the differences are
        (diff, added, skipped) = diff_dirs(d1, d2)

        print "ADDED:"
        print '\n'.join(added)

        print "\nSKIPPED:"
        print '\n'.join(skipped)
        
