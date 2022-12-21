#!/bin/sh
pip freeze > ./requirements.txt
docker image build -t wakurtosis-wsl:0.0.1 ./