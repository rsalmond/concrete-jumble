#!/bin/bash

if [ -z $1 ]; then
    printf "\nImage thingy\n\n"
    exit 1
fi

infile=/tmp/image_thing_in
outfile=/tmp/image_thing_out
fuzz=10%


cp $1 /tmp/image_thing_in

echo "first pass ..."

#XXX: in this pass filter by most common green

convert $infile -channel rgba -alpha set -fuzz $fuzz -fill none -opaque `python hist.py $infile` $outfile

cp $outfile $infile

echo "second pass ..."

#XXX: in this pass filter by most intense green

convert $infile -channel rgba -alpha set -fuzz $fuzz -fill none -opaque `python hist.py $infile` $outfile

cp $outfile test/img/out.png
