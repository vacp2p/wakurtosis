#!/bin/bash
wait_id=$1
python3 ./procfs-stats.py  --sampling-interval 1 &
$procfs_pid=$!
docker wait $wait_id
kill -15  $procfs_pid
