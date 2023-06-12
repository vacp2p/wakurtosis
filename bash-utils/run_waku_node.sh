#!/bin/sh

IP=$(ip a | grep "inet " | grep -Fv 127.0.0.1 | sed 's/.*inet \([^/]*\).*/\1/')

exec /usr/bin/wakunode --config-file="$1" --ports-shift="$2" --nat=extip:"${IP}" --log-level=TRACE