#!/bin/bash
dir=$1
wait_cid=$2
sinterval=1
pf=$dir/procfs-stats.out

python3 ./procfs-stats.py  --sampling-interval $sinterval --prefix $dir > $pf 2>&1 &
$procfs_pid=$!
docker container wait $wait_cid
kill -15  $procfs_pid   #procfs-stats is a su process
