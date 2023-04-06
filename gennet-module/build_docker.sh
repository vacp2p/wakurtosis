#!/bin/sh

rm -f traits
cp  -r ../config/traits .
docker build -t gennet .
rm -rf traits
ln  -s ../config/traits .
