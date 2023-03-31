#!/bin/bash
rclist=$1
dir=$2
wait_cid=$3
sinterval=1
proclog=$dir/docker-proc-log.out

. $rclist
#echo "$DPS_FNAME, $DINSPECT_FNAME, $PIDLIST_FNAME, $ID2VETH_FNAME" 
python3 ./procfs-stats.py  --sampling-interval $sinterval --prefix $dir > $proclog 2>&1 &
procfs_pid=$!
docker container wait $wait_cid   # now wait for the wakurtosis to finish
#sleep 5
orig_user=`logname`
chown $orig_user:$orig_user $proclog $PROCOUT_FNAME

echo "stopping procfs monitor $procfs_pid"
kill -15  $procfs_pid   # procfs-stats is a su process
