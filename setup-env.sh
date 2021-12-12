#!/bin/sh

export WORKDIR=$1
echo "WORKDIR: $WORKDIR"
export LLVM_CONFIG=llvm-config-6.0
export LLVM_COMPILER=clang

export SUBJECTS=$WORKDIR/subjects
export RESULTS=$WORKDIR/results

export AFLTEAM=$WORKDIR/aflteam

export HORSEFUZZ=$WORKDIR/horsefuzz
export HF_PATH=$WORKDIR/horsefuzz

export AFL=$WORKDIR/afl
export AFL_PATH=$WORKDIR/afl

export AFLSMART=$WORKDIR/aflsmart

export PATH=$PATH:$AFL:$HORSEFUZZ:$AFLTEAM
