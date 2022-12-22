#!/bin/sh
pip freeze > ./requirements.txt
python3 ./make_targets.py
docker image build -t wsl:0.0.1 ./