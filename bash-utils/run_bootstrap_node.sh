#!/bin/sh

IP=$(ip a | grep "inet " | grep -Fv 127.0.0.1 | sed 's/.*inet \([^/]*\).*/\1/')

exec /usr/bin/wakunode\
    --relay=true\
    --rpc-admin=true\
    --keep-alive=true\
    --max-connections=150\
    --dns-discovery=true\
    --discv5-discovery=true\
    --discv5-enr-auto-update=True\
    --log-level=INFO\
    --rpc-address=0.0.0.0\
    --metrics-server=True\
    --metrics-server-address=0.0.0.0\
    --nat=extip:${IP}