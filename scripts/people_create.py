"""

see also person-create.py

this is for creating many people entries at one time

source could be a playlist, or a list, or a cloud (list of lists)

look at a destination person directory
see if person already exists
see if any close matches exist (prompt for help resolving)
create if not
"""
import os, sys

from medley.people import Person, People, create_person
from medley.collector import Cluster


def people_create(people_root, person_term='person'):
    people = People(people_root, person_term)
    people.load()

    everything = people.cluster.flatten()
    ppl_amt = len(everything)

    ambiguous_file = os.path.join(people_root, 'meta', "ambiguous.txt")
    if os.path.exists(ambiguous_file):
        ambi = Cluster(ambiguous_file)
    else:
        ambi = Cluster()
        ambi.source = ambiguous_file
        
    total = 1
    cluster_pos = 0

    skipped = []
    for group in people.cluster:
        for item in group:
            print "Starting #%s (out of %s): %s" % (total, ppl_amt, item)
            match = people.get(item)
            amatch = ambi.contains(item)
            if not match and not amatch:
                #must not exist already...

                #make sure it's not a single name...
                #work through those later to see if we can merge them:
                parts = item.split('_')
                if len(parts) < 2:
                    #skipped.append(item)
                    ambi.add_at(item, cluster_pos)
                    ambi.save(ambiguous_file)
                    print "Automatically skipping: %s" % item

                else:
                    create_person(item, people, cluster_pos, people_root, skipped, ambi)

            elif amatch:
                #if it matched, then it's a dupe
                #and the person has already been added
                print "AMBIGUOUS TAG: %s" % item
                print ""

            else:
                #if it matched, then it's a dupe
                #and the person has already been added
                print "DUPE TAG: %s" % item
                print ""

            #print item
            total += 1

        #go back through skipped items now
        for item in skipped:
            print "item: %s" % item

        cluster_pos += 1
        print ""

    print "Total: %s" % total
        
if __name__ == '__main__':
    people_create()

