#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2013.06.05 21:46:45
# License: MIT

# Requires:
# moments

# Description:
go through all items in a playlist and determine the size the disk space that the items use

cd medley/scripts
python3 size_of_playlist_items.py /media/path/to.m3u


"""
from __future__ import print_function
import os, sys, codecs
import re

from medley.formats import M3U
from medley.helpers import load_json, get_media_properties
from medley.content import Content

from sortable.path import Path, check_ignore

def usage():
    print(__doc__)

def summarize_items(items, media_root, ignores):
    """
    Takes a list of paths to the media / files that should be summarized

    media_root is used to force a size check for a certain path
    (which allows ignoring everything else?)

    """

    #list of results for each item... can be used for csv later
    details = [ ('dimensions', 'length', 'bitrate', 'data size', 'filename'), ]
    # only include summarized results for the list here
    # (may be more than one)
    summary = [ ]

    total_size = 0
    total_items = 0
    #seconds?
    total_length = 0
    for item in items:
        # make sure it's a path
        try:
            #if it's a content item (loaded from m3u)
            item = os.path.join(item.path, item.filename)
        except:
            # otherwise just a normal path
            item = str(item)
        print("\nsize_of_list for: ", item)
        check_item = False
        #see if it's in the media_root that was passed in
        #force check in that case
        if media_root and re.match(media_root, item):
            check_item = True

        #otherwise, make sure it's not in one of the explicit ignores:
        elif not check_ignore(item, ignores):
            check_item = True

        if check_item:
            p = Path(item)
            f = p.load()

            #try:
            results = get_media_properties(item)
            cur_size = f.check_size()
            total_size += cur_size
            #except:
            #    print("missing: %s" % item)
            #else:
            if results[0] != None:
                print(results)
                results = list(results)
                results.append(cur_size)
                results.append(item)
                total_length += results[1]
                total_items += 1
                #print item
                details.append(results)
            else:
                print("skipping: %s" % item)

    print("found %s matching items" % total_items)
    summary = [ total_size, total_length, total_items ]
    return (summary, details)


def size_of_list(source, media_root=None, ignores=['/c/',]):
    """
    ignores are used to distinguish actual media from markers
    """
    items = []
    if re.search('.m3u', source):
        items = M3U(source)
        (summary, details) = summarize_items(items, media_root, ignores)
        details.insert( 0, (source, ) )
        summary.insert( 0, source )
        return ([summary, ], details)

    elif re.search('.json', source):
        loaded = load_json(source)

        #see if we have a dictionary or a list:
        if isinstance(loaded, list):
            #already have a list
            #clean it up
            for item in loaded:
                #these are usually content .json files
                #load them and then look for the media path
                content = Content(item[0])
                #print content.media
                items.append(content.media[-1][0])
            (summary, details) = summarize_items(items, media_root, ignores)
            details.insert( 0, (source, ) )
            summary.insert( 0, source )
            return ([summary, ], details)

        elif isinstance(loaded, dict):
            #walk the tree to load each item individually
            #call size_of_list() recursively
            print("dictionary found:")
            #print loaded
            summary_total = []
            details_total = []
            for child in loaded['children']:
                (summary, details) = size_of_list(child['source'])
                cur_name = child['name']
                #replace filepath with name:
                summary[0][0] = cur_name
                summary_total.extend(summary)
                details_total.extend(details)
            return (summary_total, details_total)

def main():
    #requires that at least one argument is passed in to the script itself
    #(through sys.argv)
    if len(sys.argv) > 1:
        helps = ['--help', 'help', '-h']
        for i in helps:
            if i in sys.argv:
                usage()
                exit()
        source = sys.argv[1]
        if len(sys.argv) > 2:
            media_root = sys.argv[2]
        else:
            media_root = None

        summaries, details = size_of_list(source, media_root)

        base = os.path.dirname(source)
        dest = os.path.join(base, 'summaries.csv')
        f = codecs.open(dest, 'w', encoding='utf-8')
        for summary in summaries:
            new_summary = []
            for item in summary:
                new_summary.append(str(item))
            f.write(','.join(new_summary))
            f.write('\n')
        f.close()

        dest = os.path.join(base, 'details.csv')
        f = codecs.open(dest, 'w', encoding='utf-8')
        for detail in details:
            new_detail = []
            for item in detail:
                new_detail.append(str(item))
            f.write(','.join(new_detail))
            f.write('\n')
        f.close()

        print()
        print("Details saved to: ", dest)


    else:
        usage()
        exit()

if __name__ == '__main__':
    main()
