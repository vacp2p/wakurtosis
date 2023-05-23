#!/bin/sh
image_id=$(docker images -q container-proc)
echo $image_id
docker image rm -f $image_id
docker build --rm --no-cache --progress=plain -t container-proc .
