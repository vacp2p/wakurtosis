#!/bin/bash
odir=./stats

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

echo "host-proc: gathering docker/process meta-data..."
# TODO: add more images to ancestor
dps=$odir/docker-ps.out
docker ps --no-trunc --filter "ancestor=statusteam/nim-waku"  --filter "ancestor=gowaku" --filter "ancestor=statusteam/nim-waku:nwaku-trace2" --format "{{.ID}}#{{.Names}}#{{.Image}}#{{.Command}}#{{.State}}#{{.Status}}#{{.Ports}}" > $dps

dids=$odir/docker-ids.out
cut -f 1 -d '#' $dps > $dids

dinspect=$odir/docker-inspect.out
docker inspect --format "{{.State.Pid}}{{.Name}}/{{.Image}}/{{.State}}" $(cat $dids) > $dinspect

pidlist=$odir/docker-pids.out
ps -ef | grep -E "wakunode|waku" |grep -v docker | grep -v grep | awk '{print $2}' > $pidlist

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
echo "host-proc: collected all requisite docker/process meta-data\nSignalling the /proc fs"
# *should* be non-blocking as attendant read is already issues
echo "host:proc: signal /proc fs " >  $signal_fifo


cat $signal_fifo  # blocks
# will start collecting data *before* starting WLS so that we have an idle baseline
dstats=$odir/docker-stats.out
echo "host-proc: starting the dstats monitor"
echo '# docker stats --no-trunc --format  "{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}"' > $dstats
docker stats --no-trunc --format  "{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}" $(cat $dids)  >> $dstats &
dstats_pid=$!

echo "host-proc: waiting for WLS to finish : dstats $dstats_pid is running"
docker container wait $wait_cid
sleep 60        # make sure you collect the stats until last messages settle down

echo "host-proc: stopping the docker monitor $dstats_pid"
kill -15 $dstats_pid

# only /proc collector runs as root
# TODO: only IO collector runs as root
#sudo python3 ./procfs-stats.py  --sampling-interval 1 & $collector_pid=$! & docker wait $docker_id; kill -15  $collector_pid; kill -15 $docker_pid

#usr=`id -u`
#grp=`id -g`

#sudo sh ./procfs.sh $rclist $odir $wait_cid $usr $grp
#sh   -a ./monitor_procfs.sh $rclist $odir $wait_cid
#echo "Stopping the docker monitor $dstats_pid"
#kill -15 $docker_pid
