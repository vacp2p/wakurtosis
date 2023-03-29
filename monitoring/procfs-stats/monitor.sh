#!/bin/bash
dir=stats1
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
echo $id2veth
:> $id2veth
SHELL=sh
for container in $(docker ps -q)
do
    echo $container
    iflink=`docker exec -it $container $SHELL -c 'cat /sys/class/net/eth0/iflink'`
    iflink=`echo $iflink|tr -d '\r'`
    veth=`grep -l $iflink /sys/class/net/veth*/ifindex`
    veth=`echo $veth|sed -e 's;^.*net/\(.*\)/ifindex$;\1;'`
    echo $container:$veth >> $id2veth
done

dstats=$dir/docker-stats.out
docker stats --no-trunc --format  "{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}" > $dstats &
docker_pid=$!

csize=${1:-1}
sinterval=${2:-1}

echo $csize, $sinterval
sleep 3


kill -15 $docker_pid
# only /proc collector runs as root
#sudo python3 ./procfs-stats.py --container-size $1 --sampling-interval $2
