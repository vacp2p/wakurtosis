#!/bin/bash

if [ "$#" -eq 0 ]; then
    echo "Usage: main.sh <container_name> [odir]"
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

#mkdir -p $odir

# get cpu/mem info for cross-refs
cat /proc/cpuinfo > $odir/docker-cpuinfo.out
cat /proc/meminfo > $odir/docker-meminfo.out

# get the list of running dockers
dps=$odir/docker-ps.out
filters="--filter ancestor=gowaku --filter ancestor=statusteam/nim-waku:nwaku-trace2 --filter ancestor=statusteam/nim-waku:nwaku-trace3"
docker ps --no-trunc --format "{{.ID}}#{{.Names}}#{{.Image}}#{{.Command}}#{{.State}}#{{.Status}}#{{.Ports}}" $filters > $dps


# extract the docker ids
dids=$odir/docker-dids.out
cut -f 1 -d '#' $dps > $dids

dstats=$odir/docker-stats.out
# add date and the names/versions of waku images involved
  # also add the generating command to aid parsing/debugging
echo "dstats: starting the dstats monitor"
echo "# dstats started @ $(date)" > $dstats  # clear the $dstats
echo "# images involved: $(docker images | grep waku | tr '\n' '; ' )"  >> $dstats
echo '# docker stats --no-trunc --format  "{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}"' >> $dstats
echo "ContainerID/ContainerName/ID/CPUPerc/MemUse/MemTotal/MemPerc/NetRecv/NetSent/BlockR/BlockW/PIDS"  >> $dstats

# start the docker stats
docker stats --no-trunc --format  "{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}" $(cat $dids)  >> $dstats &
dstats_pid=$!

echo "dstats: started and running as $dstats_pid"
echo "dstats: signalling WLS"
docker exec $wait_cid touch /wls/start.signal

echo "dstats: waiting for WLS to finish : dstats $dstats_pid is running"
docker container wait $wait_cid
sleep 10        # make sure you collect the stats until last messages settle down

echo "dstats: WLS finished: stopping the docker monitor $dstats_pid"
kill -15 $dstats_pid
