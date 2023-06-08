#!/bin/bash

if [ "$#" -eq 0 ]; then
    echo "Usage: main.sh <container_name> [odir] [signal_fifo]"
    echo "Will profile all running containers until the <container_name> exits"
    exit
fi

#cline=`docker ps -qa | grep  $1`  # for id
cline=` docker ps -af "name=$1" | grep $1` # for name
if [ "$cline" = "" ]; then
    echo "Error: $1 is not a valid container name"
    exit
fi

wait_cid=$1
odir=${2:-"stats"}
signal_fifo=${3:-"/tmp/hostproc-signal.fifo"}

#mkdir -p $odir

echo "host-proc: gathering hw/docker/process meta-data..."
cat /proc/cpuinfo > $odir/docker-cpuinfo.out
cat /proc/meminfo > $odir/docker-meminfo.out

# get the list of running dockers
dps=$odir/docker-ps.out
filters="--filter ancestor=gowaku --filter ancestor=statusteam/nim-waku:nwaku-trace2 --filter ancestor=statusteam/nim-waku:nwaku-trace3"
docker ps --no-trunc --format "{{.ID}}#{{.Names}}#{{.Image}}#{{.Command}}#{{.State}}#{{.Status}}#{{.Ports}}" $filters > $dps


# extract the docker ids
dids=$odir/docker-dids.out
cut -f 1 -d '#' $dps > $dids

dinspect=$odir/docker-inspect.out
docker inspect --format "{{.State.Pid}}{{.Name}}/{{.Image}}/{{.State}}" $(cat $dids) > $dinspect

#only pick up wakunodes with explicit config
pidlist=$odir/docker-pids.out
ps -ef | grep -E "wakunode|waku"  | grep config-file | awk '{print $2}' > $pidlist

cat /proc/cpuinfo > $odir/docker-cpuinfo.out
cat /proc/meminfo > $odir/docker-meminfo.out

id2veth=$odir/docker-id2veth.out
:> $id2veth
for container in `cat $dids`; do
    iflink=`docker exec $container sh -c 'cat /sys/class/net/eth0/iflink' |  tr -d '\r'`
    veth=`grep -l $iflink /sys/class/net/veth*/ifindex | sed -e 's;^.*net/\(.*\)/ifindex$;\1;'`
    echo $container:$veth >> $id2veth
done

#csize=${1:-1}
#sinterval=${2:-1}
#echo $csize, $sinterval

lif=`ip route get 1.1.1.1 | awk '{ print $5}'`

rclist=$odir/docker-rc-list.out
procout=$odir/docker-proc.out
echo "export DPS_FNAME=$dps DINSPECT_FNAME=$dinspect PIDLIST_FNAME=$pidlist ID2VETH_FNAME=$id2veth PROCOUT_FNAME=$procout LOCAL_IF=$lif WAIT_CID=$wait_cid" >  $rclist

#signal the host-proc: unblocks /proc fs
echo "host-proc: collected all requisite docker/process meta-data"
echo "host-proc: signalling the monitor"
# *should* be non-blocking as attendant read is already issued
echo "host-proc: start the /procfs" >  $signal_fifo
