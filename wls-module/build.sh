#!/bin/sh
image_id=$(docker images -q wls:0.0.1)
echo $image_id
docker image rm -f $image_id
docker image build --progress=plain  -t wls:0.0.1 ./
