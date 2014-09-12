#!/bin/bash

python /c/mindstream/mindstream/launch.py -c /c/medley code

echo "
cd /c/medley/medley/less 
lessc style.less > ../css/style.css

to launch a server:
cd /c/medley/medley 
python application.py /c/podcasts

http://localhost:8080/

if added to an init script, could use:
sudo /etc/init.d/medley start
cat /var/log/medley.log
cat /var/log/medley.err

have also been using customized watchmedo scripts
cd /c/medley/medley
watchmedo tricks tricks.yaml 

touch /c/medley/medley/application.py


python /c/mindstream/mindstream/launch.py -c /c/medley blank
python /c/mindstream/mindstream/launch.py -c /c/medley layout

python /c/mindstream/mindstream/launch.py -c /c/medley todo

python /c/mindstream/mindstream/launch.py -c /c/music/medley todo
python /c/mindstream/mindstream/launch.py -c /c/medley player


"

