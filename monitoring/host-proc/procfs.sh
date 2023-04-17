#!/bin/bash
rclist=$1
odir=$2
usr=$3
grp=$4
signal_fifo=$5

sinterval=1
proclog=$odir/docker-proc-log.out

# blocks until signalled
echo "Waiting to be signalled @ $signal_fifo: /proc fs monitor"
cat  $signal_fifo
rm $signal_fifo

# load the environ vars
. $rclist

#echo "export $DPS_FNAME $DINSPECT_FNAME $PIDLIST_FNAME $ID2VETH_FNAME $PROCOUT_FNAME $LOCAL_IF $WAIT_CID $DSTATS_PID"

echo "Starting the /proc fs monitor"
python3 ./procfs.py --sampling-interval $sinterval --prefix $odir  --wls-cid $WAIT_CID  > $proclog 2>&1 &
procfs_pid=$!
echo "Waiting on WLS : procfs $procfs_pid, docker stats $DSTATS_PID running"
docker container wait $WAIT_CID   # now wait for the wakurtosis to finish
sleep 60        # make sure you collect the stats until last messages settle down

echo "Stopping /proc fs monitor $procfs_pid"
kill -15  $procfs_pid   # procfs-stats is a su process

echo "Stopping the docker monitor $DSTATS_PID"
kill -15 $DSTATS_PID

echo "Updating the owner of logs: $usr, $grp"
chown $usr:$grp $proclog $PROCOUT_FNAME
