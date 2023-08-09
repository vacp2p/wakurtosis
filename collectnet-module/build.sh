#!/bin/sh
image_id=$(docker images -q collectnet:latest)
echo $image_id
docker image rm -f $image_id
docker image build --progress=plain  -t collectnet .
