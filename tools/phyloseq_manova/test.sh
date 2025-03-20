#!/bin/sh
FROGS_DIR=`dirname $(dirname $(pwd))`
export PATH=$FROGS_DIR/libexec:$PATH
export PYTHONPATH=$FROGS_DIR/lib:$PYTHONPATH

if [ -d test ]
then
  rm -r test/*
else
  mkdir test
fi 

./phyloseq_manova.py --phyloseq-rdata data/data.Rdata \
                   --var-exp "EnvType + FoodType" \
                   --distance-matrix data/Unifrac.tsv \
                   --html test/phylo_manova.nb.html \
                   --log-file test/phylo_manova.log
