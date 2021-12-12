#!/bin/bash

SRC_FOLDER=$1
OUTPUT_FILE=gcov.log

cd $SRC_FOLDER

rm -f $OUTPUT_FILE
touch $OUTPUT_FILE

for f in $(find ./ -name "*.gcno")
do 
  gcov -b -f $f >> $OUTPUT_FILE
done 
