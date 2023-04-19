#!/bin/sh

rm -f traits
rm -rf network_data
cp  -r ../config/traits .
docker build -t gennet .
rm -rf traits
ln  -s ../config/traits .
