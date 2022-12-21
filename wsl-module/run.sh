#!/bin/sh
python3 ./make_targets.py
docker cp targets.json wakurtosis-wsl:0.0.1:/targets.json
docker run wakurtosis-wsl:0.0.1