#!/bin/bash
rclist=$1
odir=$2
usr=$3
grp=$4
signal_fifo=$5

sinterval=1
proclog=$odir/docker-proc-log.out

# blocks until signalled
echo "host-proc: /proc fs monitor : waiting on $signal_fifo"
cat  $signal_fifo

export SIGNAL_FIFO=$signal_fifo
# load the environ vars
. $rclist

#echo "export $DPS_FNAME $DINSPECT_FNAME $PIDLIST_FNAME $ID2VETH_FNAME $PROCOUT_FNAME $LOCAL_IF $WAIT_CID"


# 10k * 10 /proc entries per process
max_wakunodes=10000
nfh=$((10*max_wakunodes))
ulimit -n $nhf    # jack-up the number of files handles for all the children

echo "host-proc: starting the /proc fs monitor"
python3 ./procfs.py --sampling-interval $sinterval --prefix $odir --wls-cid $WAIT_CID  > $proclog 2>&1 &
procfs_pid=$!
echo "host-proc: waiting for WLS to finish: procfs $procfs_pid running"
docker container wait $WAIT_CID   # now wait for the wakurtosis to finish
sleep 60        # make sure you collect the stats until last messages settle down

echo "host-proc: stopping /proc fs monitor $procfs_pid"
kill -15  $procfs_pid   # procfs-stats is a su process

echo "host-proc: updating the owner of logs: $usr, $grp"
chown $usr:$grp $proclog $PROCOUT_FNAME
