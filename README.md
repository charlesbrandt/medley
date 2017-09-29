==============
Medley
==============

Medley: "a mixture, especially of heterogeneous elements; hodgepodge; jumble."

Medley helps sort through collections of content.

Welcome to Medley!

Medley has 3 main parts:

- A python library for storing and sorting meta data for content
- A Qt based, cross platform, media player to help tag media.
- A locally hosted web based application for sorting and finding content. 

The easiest place to start is with the Medley Player.

    cd /path/to/medley/player

for example:

    cd /c/medley/player/
    #make sure it's a blank start
    cp blank.json configs.json
    ./player.py 


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


