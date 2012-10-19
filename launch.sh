#!/bin/bash

python /c/mindstream/mindstream/launch.py -c /c/medley todo

echo "
python /c/mindstream/mindstream/launch.py -c /c/medley blank

python /c/mindstream/mindstream/launch.py -c /c/medley code
python /c/mindstream/mindstream/launch.py -c /c/medley layout


to launch a server:
cd /c/medley/medley 
python application.py /c/podcasts

http://localhost:8080/

cd /c/podcasts/beats_in_space/2012/20120417/
python /c/medley/scripts/mpb_to_m3u.py 20120417.mpb 20120417.m3u

cd /c/podcasts/beats_in_space
python m3u_to_marks.py 2012/20120417/20120417.m3u
"

