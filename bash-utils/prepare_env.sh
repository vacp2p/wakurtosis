#!/bin/sh

kurtosis engine stop

ulimit -n $(ulimit -n -H)
ulimit -u $(ulimit -u -H)

sudo sysctl -w net.ipv4.neigh.default.gc_thresh3=4096
sudo sysctl fs.inotify.max_user_instances=1048576
sudo sysctl -w vm.max_map_count=262144

sudo docker container rm -f $(docker container ls -aq)
sudo docker volume rm -f $(docker volume ls -q)

kurtosis engine start