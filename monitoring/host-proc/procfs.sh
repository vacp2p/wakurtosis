#!/bin/bash
rclist=$1
odir=$2
wait_cid=$3
usr=$4
grp=$5

sinterval=1
proclog=$odir/docker-proc-log.out


. $rclist
#echo "$DPS_FNAME, $DINSPECT_FNAME, $PIDLIST_FNAME, $ID2VETH_FNAME"

echo "Starting the /proc fs monitor"
python3 ./procfs.py --sampling-interval $sinterval --prefix $odir  --wls-cid $wait_cid  > $proclog 2>&1 &
procfs_pid=$!
echo "Waiting on WLS : procfs $procfs_pid running"
docker container wait $wait_cid   # now wait for the wakurtosis to finish
sleep 60        # make sure you collect the stats until last messages settle down

echo "Stopping /proc fs monitor $procfs_pid"
kill -15  $procfs_pid   # procfs-stats is a su process

echo "Updating the owner of the output files: $usr, $grp"
chown $usr:$grp $proclog $PROCOUT_FNAME

