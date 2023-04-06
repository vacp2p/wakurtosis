#!/bin/bash
dir=./monitoring/procfs-stats/stats

if [ "$#" -ne 1 ]; then
    echo "Usage: monitor.sh <container_name>"
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

mkdir -p $dir

# TODO: add more images to ancestor
dps=$dir/docker-ps.out
docker ps --no-trunc --filter "ancestor=statusteam/nim-waku"  --filter "ancestor=gowaku" --filter "ancestor=statusteam/nim-waku:nwaku-trace2" --format "{{.ID}}#{{.Names}}#{{.Image}}#{{.Command}}#{{.State}}#{{.Status}}#{{.Ports}}" > $dps

dinspect=$dir/docker-inspect.out
docker inspect --format "{{.State.Pid}}{{.Name}}/{{.Image}}/{{.State}}" $(docker ps -q) > $dinspect

pidlist=$dir/docker-pids.out
ps -ef | grep -E "wakunode|waku" |grep -v docker | grep -v grep | awk '{print $2}' > $pidlist

cat /proc/cpuinfo > $dir/docker-cpuinfo.out
cat /proc/meminfo > $dir/docker-meminfo.out

id2veth=$dir/docker-id2veth.out
:> $id2veth
SHELL=sh
for container in $(docker ps --no-trunc  | grep -E "gowaku|nim-waku"   |  awk '{print $1}'); do
    iflink=`docker exec -it $container sh -c 'cat /sys/class/net/eth0/iflink' |  tr -d '\r'`
    veth=`grep -l $iflink /sys/class/net/veth*/ifindex | sed -e 's;^.*net/\(.*\)/ifindex$;\1;'`
    echo $container:$veth >> $id2veth
done

# TODO: add more images to grep
dstats=$dir/docker-stats.out
echo '# docker stats --no-trunc --format  "{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}"' > $dstats
docker stats --no-trunc --format  "{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}" | grep -E "gowaku|nim-waku|containers"  >> $dstats &
docker_pid=$!

#csize=${1:-1}
#sinterval=${2:-1}
#echo $csize, $sinterval

lif=`ip route get 1.1.1.1 | awk '{ print $5}'`

rclist=$dir/docker-rc-list.out
procout=$dir/docker-proc.out
echo "export DPS_FNAME=$dps DINSPECT_FNAME=$dinspect PIDLIST_FNAME=$pidlist ID2VETH_FNAME=$id2veth PROCOUT_FNAME=$procout LOCAL_IF=$lif" >  $rclist

# only /proc collector runs as root
# TODO: only IO collector runs as root
#sudo python3 ./procfs-stats.py  --sampling-interval 1 & $collector_pid=$! & docker wait $docker_id; kill -15  $collector_pid; kill -15 $docker_pid

sudo sh ./monitoring/procfs-stats/monitor_procfs.sh $rclist $dir $wait_cid
#sh   -a ./monitor_procfs.sh $rclist $dir $wait_cid
echo "stopping docker monitor $docker_pid"
kill -15 $docker_pid
