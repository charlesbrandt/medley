"""
common files needed to help with source scraping operations

"""

import re, os, codecs, subprocess, time, sqlite3
#import logging

#urllib.retrieve:
import urllib
import urllib2
import urlparse
import cookielib

from moments.timestamp import Timestamp
from moments.path import Path

try:
    import json
except:
    try:
        import simplejson as json
    except:
        raise ValueError, "NO JSON"

from yapsy.IPlugin import IPlugin

class Scraper(IPlugin):
    """
    Parent class for all other Scraper / Synchronizer plugins
    for use with Medley and Collections

    probably won't use 'self' in this object much
    but it does make it easier to collect common functions together

    Used at a similar level as CollectionSummary
    (they could even use the same json data file to store settings)
    but keeping separate since the functions target different stages.
    """

    def get_all_cookies(self, cookie_db):
        CONTENTS = "host, path, isSecure, expiry, name, value"
        cj = cookielib.LWPCookieJar()       # This is a subclass of FileCookieJar that has useful load and save methods
        con = sqlite3.connect(cookie_db)
        cur = con.cursor()
        sql = "SELECT {c} FROM moz_cookies".format(c=CONTENTS)
        cur.execute(sql)
        for item in cur.fetchall():
            c = cookielib.Cookie(0, item[4], item[5],
                None, False,
                item[0], item[0].startswith('.'), item[0].startswith('.'),
                item[1], False,
                item[2],
                item[3], item[3]=="",
                None, None, {})
            #print c
            cj.set_cookie(c)
        return cj

    def download_alt(self, url, dest):
        """
        attempt at making a cookie aware, password aware, download helper
        ended up just using the browser to save the file automatically
        """
        COOKIE_DB = "{home}/.mozilla/firefox/cookies.sqlite".format(home=os.path.expanduser('~'))
        #cj = cookielib.MozillaCookieJar()
        #cj.load(os.path.join(os.path.expanduser("~"), ".netscape", "cookies.txt"))
        #cj.load(os.path.join(os.path.expanduser("~"), ".netscape", "cookies.txt"))
        #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        cj = get_all_cookies(COOKIE_DB)


        # create a password manager
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

        # Add the username and password.
        # If we knew the realm, we could use it instead of None.
        password_mgr.add_password(realm='None',
                  uri='http://login.domian.com',
                  user='username',
                  passwd='password')

        handler = urllib2.HTTPBasicAuthHandler(password_mgr)

        # create "opener" (OpenerDirector instance)
        opener = urllib2.build_opener(handler, urllib2.HTTPCookieProcessor(cj))

        # use the opener to fetch a URL
        #opener.open(a_url)

        #url = "http://download.thinkbroadband.com/10MB.zip"

        #file_name = url.split('/')[-1]
        #u = urllib2.urlopen(url)
        u = opener.open(url)
        f = open(dest, 'w')
        meta = u.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        print "Downloading: %s Bytes: %s" % (url, file_size)

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break

            file_size_dl += block_sz
            f.write(buffer)
            status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            status = status + chr(8)*(len(status)+1)
            print status,

        f.close()

    def download(self, url, dest):
        """
        very simple download that wraps python's urllib.urlretrieve() call
        """

        #*2011.06.29 21:40:11 download_file python 
        #http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
        #urllib.urlretrieve ("http://www.example.com/songs/mp3.mp3", "mp3.mp3")

        urllib.urlretrieve(url, dest)


    def download_with_browser(self, driver, link, browser_root='/Users/user/Downloads/', filename=None):
        """
        specialized download routine to use the browser to save files
        then poll for the file to be complete before moving on

        driver is an instance of a selenium/webdriver instance running a browser 

        if the download stalls, move on after a threshold is met

        this does not handle moving the file
        only returns true or false depending on if the file needed to be skipped
        because it stalled out.

        browser_root is the default location that browser is configured
        to download to
        browser should be set to automatically download files
        of the type you are downloading in order to speed up the process
        """
        skipped = False

        #*2011.12.30 13:28:09
        #sometimes it's not possible to know the filename
        #until after you start the download
        #(that is, it only shows up in the directory.)
        #
        #to work around that, 
        #get the current files in the directory before starting the download
        #then look after and see what the difference is
        pre_files = os.listdir(browser_root)

        #this kicks off the actual download:
        driver.get(link)

        #make sure there has been time for .part to be created
        time.sleep(30)

        post_files = os.listdir(browser_root)
        new_files = []
        for f in post_files:
            if f not in pre_files:
                new_files.append(f)
        print "found these new files: %s" % new_files
        assert len(new_files) < 3 and len(new_files) > 0

        for f in new_files:
            if not re.search('\.part', f):
                filename = f

        download_dest = os.path.join(browser_root, filename)
        dpart = download_dest + '.part'

        #start = Timestamp()
        stall_start = None
        stalled = False
        size = 0
        new_size = -1

        dpartp = Path(dpart)
        #there is a chance it finished downloading if the file was small
        if dpartp.exists():
            dpartf = dpartp.load()
            while dpartp.exists():
                #do this before the sleep to make sure it's still there
                new_size = dpartf.check_size()
                time.sleep(10)

                #if the size has changed, something is happening
                #not stalled
                if new_size != size:
                    if stalled:
                        now = Timestamp()
                        print "download resumed: %s" % now

                    stalled = False
                    size = new_size
                #could just be slow to download, but want to at least check
                else:
                    #we've already set it before
                    if stalled:
                        #check if stall_start was 25 minutes ago

                        now = Timestamp()
                        if now.datetime > stall_start.future(minutes=25).datetime:
                            print "stall threshold met. deleting: %s" % dest
                            dpartp.remove()
                            dpath.remove()
                            #if we get here, we know it didn't work
                            skipped = True

                            #log skips to make sure we go back:
                            skip_dest = os.path.join(browser_root, "skips.txt")
                            skip_file = codecs.open(skip_dest, 'a', encoding='utf-8', errors='ignore')
                            skip_file.write(o)
                            skip_file.write("\n")
                            skip_file.write(json.dumps(scene))
                            skip_file.write("\n")
                            skip_file.close()
                    else:
                        stalled = True
                        stall_start = Timestamp()
                        print "download stalled since: %s" % stall_start
        if not skipped:
            return filename
        else:
            return skipped

    def move_download(self, source, destination):
        """
        if using download with browser,
        the file usually ends up in a default location

        one fix is to move the file after downloading it to the desired location
        """

        escaped_dest = destination.replace(' ', '\\ ')
        command = "mv %s %s" % (str(source), escaped_dest)
        #print command
        mv = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        mv.wait()
        #print "moved file to: %s" % dest



    def save_current(self, driver, destination='./', page_id=1, prefix="site_name"):
        if not os.path.exists(destination):
            os.makedirs(destination)        

        #page = driver.get_page_source()
        page = driver.page_source
        #print page

        #save the resulting page
        ts = Timestamp()
        page_name = '%s-%s-%s.html' % (prefix, page_id, ts.compact(accuracy="minute"))
        page_path = os.path.join(destination, page_name)
        #html = file(page_name, 'w')
        html = codecs.open(page_path, 'w', encoding='utf-8', errors='ignore')
        html.write(page)
        html.close()

        return page_path

    #main / common scraping routines
    #these need to be customized for the source
    
    def update_index(self, url, destination):
        raise ValueError, "Define in subclass"

    def get_details(self, items, destination, url_root):
        """
        download and parse details for a specific content item
        """
        raise ValueError, "Define in subclass"

    def parse_details(self, page_path, item=None):
        """
        given a previously download page, generate json content data from it
        """
        raise ValueError, "Define in subclass"

    def download_items(self, items):
        raise ValueError, "Define in subclass"

    def local_index(self):
        """
        render html for use in medley
        these are always custom for the type of collection involved
        """
        pass

    def local_item(self):
        pass
