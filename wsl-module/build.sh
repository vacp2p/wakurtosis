#!/bin/sh
pip freeze > ./requirements.txt
docker image build -t wsl:0.0.1 ./