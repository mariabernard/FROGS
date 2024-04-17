#!/bin/sh
FROGS_DIR=`dirname $(dirname $(pwd))`
export PATH=$FROGS_DIR/libexec:$PATH
export PYTHONPATH=$FROGS_DIR/lib:$PYTHONPATH

# Create output folder
if [ ! -d "test" ]
then
    mkdir test
else
    rm -r test
fi

##############
# FROGS_tree #
##############

# # arbre mafft
mkdir -p test/mafft
./tree.py --input-fasta data/sequences.fasta \
    --input-biom data/sequences.biom \
    --html test/mafft/summary.html \
    --output-tree test/mafft/frogs.nwk --log-file test/mafft/tree.log
