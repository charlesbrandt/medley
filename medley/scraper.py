"""
common files needed to help with source scraping operations

rather than using a class object with plugins (scraper-old.py)

just making the main parts functions that can be imported...
that should be much easier to use for other scripts that need them
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

from content import SimpleContent

def download_image(url, destination_path, tags=[], alt_name="image", people=[], drive_dir=None, base_dir=None):
    """
    separating functionality for downloading just one image...
    might make sense to do the looping externally in some cases

    download the image at the url to the destination_path directory
    update name if needed
    """
    
    print
    print url
    #find original filename... should be in the url
    path_parts = url.split('/')
    suffix_parts = path_parts[-1].split('?')
    more_parts = suffix_parts[0].split(':')
    file_name = more_parts[0]

    file_name = file_name.replace(' ', '_')
    file_name = file_name.replace('%20', '_')
    file_name = file_name.replace('(', '')
    file_name = file_name.replace(')', '')

    #print file_name
    name_parts = file_name.split('.')

    #if the name is generic, at least name it for the person:
    generics = ['original', 'temp', 'photo', 'image', 'picture']
    for option in generics:
        if re.match(option, name_parts[0], re.I):
            print "Updating: %s to %s" % (file_name, alt_name)
            name_parts[0] = alt_name

    extension = name_parts[-1].lower()
    if not extension in [ 'jpg', 'jpeg', 'png', 'gif', 'tif' ]:
        #just give it something
        print "Unrecognized extension: %s, adding .jpg" % (extension)
        name_parts.append('jpg')

    file_name = '.'.join(name_parts)

    download = os.path.join(destination_path, "temp.image")
    if os.path.exists(download):
        print
        print url
        print download
        raise ValueError, "Temp image already exists. Not overwriting"

    #print download

    #go ahead and download it now:
    urllib.urlretrieve(url, download)

    download_size = os.path.getsize(download)

    #now move the downloaded file into place...
    cur_name = file_name
    existing = True
    duplicate = False
    index = 1
    #loop until we figure out if we already have it,
    #or find a valid new file name
    while existing:
        new_dest = os.path.join(destination_path, cur_name)
        if os.path.exists(new_dest):
            #if the file_name already exists,
            #check if it is the same (compare file size)
            dest_size = os.path.getsize(new_dest)
            if download_size == dest_size:
                #if its the same simply delete the temp one...
                print "Already had: %s" % url
                os.remove(download)
                existing = False
                duplicate = True
            else:
                #if not, create a new name for it (and try again)
                prefix = "%s-%04d" % (alt_name, index)
                name_parts[0] = prefix
                cur_name = '.'.join(name_parts)
                index += 1
        else:
            #found one that will work
            existing = False

    if not duplicate:
        #otherwise
        #move to safe filename,
        os.rename(download, new_dest)

    #then create appropriate json file for meta data
    content = SimpleContent()

    if drive_dir:
        content.drive_dir = drive_dir
    else:
        content.drive_dir = destination_path

    if base_dir and drive_dir:
        content.base_dir = base_dir
    elif base_dir:
        raise ValueError, "If specifying a base_dir (%s), specify a drive_dir (%s) too!" % (drive_dir, base_dir)
    else:
        content.base_dir = ""

    content.filename = cur_name
    content.added = Timestamp()
    content.tags = tags
    content.sites.append(url)
    content.people.extend(people)
    content.make_hash()

    #make sure we have an extension:
    if len(name_parts) > 1:
        name_parts[-1] = 'json'
    else:
        name_parts.append('json')
    json_file = '.'.join(name_parts)
    content.json_source = os.path.join(destination_path, json_file)
    content.save()

    return cur_name

def download_images(urls, destination_path, tags=[], alt_name="image", people=[], drive_dir=None, base_dir=None):
    """
    take a list of urls
    download each of them to the destination_path directory
    update names if needed
    """
    results = []
    
    #for url in urls[:1]:
    for url in urls:
        if url:
            cur_name = download_image(url, destination_path, tags, alt_name, people, drive_dir, base_dir)
            results.append(cur_name)

    return results



def get_all_cookies(cookie_db):
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

def download_alt(url, dest):
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

def download(url, dest):
    """
    very simple download that wraps python's urllib.urlretrieve() call
    """

    #*2011.06.29 21:40:11 download_file python 
    #http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
    #urllib.urlretrieve ("http://www.example.com/songs/mp3.mp3", "mp3.mp3")

    urllib.urlretrieve(url, dest)


def download_with_browser(driver, link, browser_root='/Users/user/Downloads/', filename=None):
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

def move_download(source, destination):
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



def save_current(driver, destination='./', page_id=1, prefix="site_name"):
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
