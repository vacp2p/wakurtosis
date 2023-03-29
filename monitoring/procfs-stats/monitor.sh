#!/bin/bash
dir=stats1

if [ "$#" -ne 1 ]; then
    echo "Usage: monitor.sh <container_id>"
    echo "Will profile all running containers until the <container_id> exits"
    exit
fi

cline=`docker ps -qa | grep  $1`
if [ "$cline" = "" ]; then
    echo "Error: $1 is not a valid container id"
    exit
fi

wait_cid=$1

mkdir -p $dir

dps=$dir/docker-ps.out
docker ps --no-trunc --filter "ancestor=statusteam/nim-waku"  --filter "ancestor=gowaku" --format "{{.ID}}#{{.Names}}#{{.Image}}#{{.Command}}#{{.State}}#{{.Status}}#{{.Ports}}" > $dps

dinspect=$dir/docker-inspect.out
docker inspect --format "{{.State.Pid}}{{.Name}}/{{.Image}}/{{.State}}" $(docker ps -q) > $dinspect

pidlist=$dir/docker-pids.out
ps -ef | grep -E "wakunode|waku" |grep -v docker | grep -v grep | awk '{print $2}' > $pidlist

cat /proc/cpuinfo > $dir/docker-cpuinfo.out
cat /proc/meminfo > $dir/docker-meminfo.out

id2veth=$dir/docker-id2veth.out
:> $id2veth
SHELL=sh
for container in $(docker ps -q); do
    iflink=`docker exec -it $container sh -c 'cat /sys/class/net/eth0/iflink' |  tr -d '\r'`
    veth=`grep -l $iflink /sys/class/net/veth*/ifindex | sed -e 's;^.*net/\(.*\)/ifindex$;\1;'`
    echo $container:$veth >> $id2veth
done

dstats=$dir/docker-stats.out
docker stats --no-trunc --format  "{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}" > $dstats &
docker_pid=$!

#csize=${1:-1}
#sinterval=${2:-1}
#echo $csize, $sinterval
sleep 3

# only /proc collector runs as root
#sudo python3 ./procfs-stats.py  --sampling-interval 1 & $collector_pid=$! & docker wait $docker_id; kill -15  $collector_pid; kill -15 $docker_pid

#sudo ./monitor_procfs.sh $dir $wait_cid
kill -15 $docker_pid
