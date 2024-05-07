#!/bin/bash
FROGS_DIR=`dirname $(dirname $(pwd))`
export PATH=$FROGS_DIR/libexec:$PATH
export PYTHONPATH=$FROGS_DIR/lib:$PYTHONPATH

# Create output folder
if [ ! -d "test" ]
then
    mkdir test
fi

./frogsfunc_placeseqs.py \
    --input-fasta data/frogsfunc.fasta \
    --input-biom data/frogsfunc.biom \
    --placement-tool sepp \
    --output-tree test/25-frogsfunc_placeseqs_tree.nwk \
    --excluded test/25-frogsfunc_placeseqs_excluded.txt \
    --output-fasta test/25-frogsfunc_placeseqs.fasta \
    --output-biom test/25-frogsfunc_placeseqs.biom \
    --closests-ref test/25-frogsfunc_placeseqs_closests_ref_sequences.txt \
    --output-marker test/25-frogsfunc_marker.tsv \
    --html test/25-frogsfunc_placeseqs_summary.html
