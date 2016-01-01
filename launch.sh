#!/bin/bash

launch.py -c /c/public/medley code

#not used:
#launch.py -c /c/medley todo

echo "
cd /c/public/medley/medley/less 
lessc style.less > ../css/style.css

to launch a server:
cd /c/public/medley/server
python application.py /c/podcasts

http://localhost:8080/

if added to an init script, could use:
sudo /etc/init.d/medley start
cat /var/log/medley.log
cat /var/log/medley.err

have also been using customized watchmedo scripts
cd /c/public/medley/medley
watchmedo tricks tricks.yaml 

touch /c/public/medley/medley/application.py


launch.py -c /c/public/medley layout
launch.py -c /c/public/medley server

launch.py -c /c/public/medley player

launch.py -c /c/public/medley auto_playlist
launch.py -c /c/public/medley split_media
launch.py -c /c/public/medley extract_playlist
launch.py -c /c/public/medley scripts

launch.py -c /c/public/medley blank
launch.py -c /c/public/medley start_here
launch.py -c /c/music/medley todo

launch.py -c /c/public/medley people
launch.py -c /c/public/medley people_web

"

