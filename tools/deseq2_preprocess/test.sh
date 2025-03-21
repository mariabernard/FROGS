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

# DESeq2 preprocess with ASV abundances 
echo ""
OUT=test/deseq2_asv
echo $OUT "DESeq2 asv abundances"
mkdir -p $OUT

./deseq2_preprocess.py \
 --phyloseq-rdata data/data.Rdata \
 --analysis ASV \
 --log-file $OUT/deseq2_preprocess_ASV.log \
 --out-deseq-rdata $OUT/deseq2_preprocess_ASV.Rdata \
 --var-exp EnvType 


# DESeq2 preprocess with ASV abundances 
echo ""
OUT=test/deseq2_func
echo $OUT "DESeq2 function abundances"
mkdir -p $OUT

./deseq2_preprocess.py \
 --sample-metadata-tsv data/chaillou.sample \
 --input-functions data/frogsfunc_functions_unstrat_EC.tsv \
 --analysis FUNCTION \
 --log-file $OUT/deseq2_preprocess_func.log \
 --out-deseq-rdata $OUT/deseq2_preprocess_func.Rdata \
 --out-phyloseq-rdata $OUT/phyloseq_functions.Rdata \
 --var-exp EnvType
