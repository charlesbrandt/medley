"""
thin command line wrapper around medley.people.create_person function

specify name to create as parameter on command line

assumes parent directory and cloud structure are already in place
#may want to make this into a script:

export CIRCLE=musicians
mkdir -p /c/people/$CIRCLE/meta
touch /c/people/$CIRCLE/meta/people.txt
#make a blank moments entry with cloud_tag
emacs /c/people/$CIRCLE/meta/people.txt
echo "python /c/medley/scripts/person-create.py /c/people/$CIRCLE $CIRCLE <>"

#python person-create.py /c/path/to/people/ cloud_tag person_tag

#if cloud_tag not specified, assumes the basename of the path to be the tag:
python person-create.py /c/path/to/people/ person_tag [cloud_tag]

"""
from __future__ import print_function
import os, sys

from medley.people import Person, People, create_person
#this is not used here, but for more involved scripts it could be useful
#from medley.collector import Cluster

def usage():
    print(__doc__)
    
def main():
    if len(sys.argv) > 1:
        helps = ['--help', 'help', '-h']
        for i in helps:
            if i in sys.argv:
                usage()
                exit()
        root = sys.argv[1]
        item = sys.argv[2]

    else:
        usage()
        exit()

    if len(sys.argv) > 3:
        cloud_tag = sys.argv[3]
    else:
        if root[-1] == '/':
            root = root[:-1]
        cloud_tag = os.path.basename(root)

    people = People(root, cloud_tag)
    people.load()

    #won't be using these here
    cluster_pos = 1
    skipped = []
    ambi = []
    
    create_person(item, people, cluster_pos, root, skipped, ambi)
        
if __name__ == '__main__':
    main()

