#!/bin/sh
pip freeze > ./requirements.txt
docker image build --progress=plain  -t wsl:0.0.1 ./