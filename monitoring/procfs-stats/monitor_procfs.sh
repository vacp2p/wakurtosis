#!/bin/bash
rclist=$1
dir=$2
wait_cid=$3
usr=$4
grp=$5

sinterval=1
proclog=$dir/docker-proc-log.out

. $rclist
#echo "$DPS_FNAME, $DINSPECT_FNAME, $PIDLIST_FNAME, $ID2VETH_FNAME"

echo "starting the python"
python3 ./monitoring/procfs-stats/procfs-stats.py --sampling-interval $sinterval --prefix $dir > $proclog 2>&1 &
procfs_pid=$!
echo "Waiting for WLS to finish"
#docker container wait $wait_cid   # now wait for the wakurtosis to finish
sleep 60

echo "stopping procfs monitor $procfs_pid"
kill -15  $procfs_pid   # procfs-stats is a su process

echo "update the owner of the output files: $usr, $grp"
chown $usr:$grp $proclog $PROCOUT_FNAME

