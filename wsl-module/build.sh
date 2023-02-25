#!/bin/sh
# pip freeze > requirements.txt
image_id=$(docker images -q wsl:0.0.1)
echo $image_id
docker image rm -f $image_id
docker image build --progress=plain  -t wsl:0.0.1 ./
