#!/bin/bash

echo 'YAMNet sound analysis'

if [[ $# -ne 1 ]] ; then
    echo 'Usage: '$0' Video_or_Audio_File'
    exit 1
fi

inputfull=`realpath $1`
echo $inputfull
ipath=$(dirname -- "$inputfull")
echo $ipath
filename=$(basename -- "$inputfull")
echo $filename

docker run --rm -it --name yamnet -v $ipath:/data hagt/yamnet:1.0 "/data/$filename"

