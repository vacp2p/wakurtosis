#!/bin/sh
# pip freeze > requirements.txt
docker image build --progress=plain  -t gennet:0.0.1 ./
