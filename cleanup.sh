#!/bin/sh
enclave_name=${1:-"wakurtosis"}
# hardcoded files/fifo/folders
rm -f   ./kurtosisrun_log.txt
rm -f /tmp/hostproc-signal.fifo
rm -rf  ./wakurtosis_logs ./config/topology_generated  ./monitoring/host-proc/stats

docker stop gennet cadvisor bootstrap_node > /dev/null  2>&1
docker rm gennet cadvisor bootstrap_node > /dev/null  2>&1

kurtosis  --cli-log-level "error" enclave rm -f $enclave_name > /dev/null 2>&1

docker stop $(docker ps -qa)  > /dev/null 2>&1
docker rm $(docker ps -qa)  > /dev/null 2>&1

toml_file="config/traits/discv5.toml"
sed -i "s/^discv5-bootstrap-node=\".*\"$/discv5-bootstrap-node=""/" "$toml_file"
