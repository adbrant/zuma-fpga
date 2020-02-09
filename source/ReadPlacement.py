
# use this if you want to include modules from a subforder
import os, sys, inspect
cmd_subfolder = os.path.realpath(os.path.abspath( os.path.join(os.path.split \
(inspect.getfile( inspect.currentframe() ))[0],"VprParsers")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import globs
import PlacementParser

## Parse the placement file and transfer the information to internal structures.
# The placement file contains the location of the different cluster
# and their netlist names.
# These names are later used in the netlist file,
# which describe the inner routing of each cluster.
# So we parse this names for the later parsing of the netlist.
# @param filename The filename of the placement file, e.g place.p.
def read_placement(filename):

    blocks = PlacementParser.parsePlacement(filename)

    for block in blocks:

        # skip ios
        if block.location[0] in [0, globs.clusterx] \
        or block.location[1] in [0, globs.clustery]:
            continue

        #write the name of the block in an Cluster object
        else:
            #write the netlist name in the correct location of the cluster array
            globs.clusters[block.location].CLB = block.name #name
