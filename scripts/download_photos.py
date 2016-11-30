"""
*2014.11.22 12:03:26
simple script that takes a list of links and downloads all of them to the current directory
along the way it creates a meta data file for each, so sources can be tracked

see also [2014.11.12 10:37:17]

would be nice to have a simple Qt interface for this too
"""
import os, re

from medley.scraper import download_images

#copy this
urls = """
"""
destination = ''
tags = []
alternate_name = ''

#paste, then delete:



urls = urls.splitlines()
download_images(urls, destination, tags, alternate_name)
