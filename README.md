==============
Medley
==============

Medley has 3 main parts:

- A python library for storing and sorting meta data for content
- A Qt based, cross platform, media player to help tag media.
- A locally hosted web based application for sorting and finding content. 

Getting started with Medley may seem daunting. There are many places where media and its meta data get scattered.  Hang in there... you'll be up and running soon. 

The easiest place to start is with the Medley Player.

cd /path/to/medley/player
for example:
cd /c/medley/player/
#make sure it's a blank start
cp blank.json configs.json
./player-vlc.py 



I was going to call this package Collections, but that conflicts with the standard library module with the same name.  Medley: "a mixture, especially of heterogeneous elements; hodgepodge; jumble." Close enough!  Welcome to Medley.

Medley helps sort through collections or medleys of content.


- Make sure that the media you want to sort is available locally somehow (mount the drive, connect to the shared repository, etc).
Ideally this location is the same on all machines to make playlists compatible.


DOCS
---------
A (very early) start for documentation can be found in:
docs/


To generate the documentation, you will need Sphinx:
sudo easy_install sphinx

cd docs/
sphinx-build -b html . ./_build/html/

or
make html

INSTALL
----------

see docs/installation.txt

and

docs/_build/html/installation.html


CONTRIBUTORS
-----------------


THANKS ALSO TO
-----------------


