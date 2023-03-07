#!/bin/sh
FROGS_DIR=`dirname $(dirname $(pwd))`
export PATH=$FROGS_DIR/libexec:$FROGS_DIR/app:$PATH
export PYTHONPATH=$FROGS_DIR/lib:$PYTHONPATH

# Create output folder
if [ ! -d "test" ]
then
    mkdir test
else
    rm -r test/*
fi

# DESeq2 preprocess with OTU abundances 
echo ""
OUT=test/deseq2_otu
echo $OUT "DESeq2 otu abundances"
mkdir -p $OUT

./deseq2_preprocess.py \
 --data data/data.Rdata \
 --analysis OTU \
 --log-file $OUT/deseq2_preprocess_OTU.log \
 --out-Rdata $OUT/deseq2_preprocess_OTU.Rdata \
 --var EnvType

# DESeq2 preprocess with OTU abundances 
echo ""
OUT=test/deseq2_func
echo $OUT "DESeq2 function abundances"
mkdir -p $OUT

./deseq2_preprocess.py \
 --samplefile data/chaillou.sample \
 --input-functions data/frogsfunc_functions_unstrat_EC.tsv \
 --analysis FUNC \
 --log-file $OUT/deseq2_preprocess_func.log \
 --out-Rdata $OUT/deseq2_preprocess_func.Rdata \
 --out-Phyloseq $OUT/phyloseq_functions.Rdata \
 --var EnvType