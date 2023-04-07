#!/bin/sh
enclave_name=${1:-"wakurtosis"}
rm -f   ./kurtosisrun_log.txt
rm -rf  ./wakurtosis_logs ./config/topology_generated  ./monitoring/procfs-stats/stats
# hardcoded folders
docker stop gennet cadvisor > /dev/null  2>&1
docker rm gennet cadvisor > /dev/null  2>&1
kurtosis  --cli-log-level "error" enclave rm -f $enclave_name > /dev/null 2>&1
docker stop $(docker ps -qa)  > /dev/null 2>&1
docker rm $(docker ps -qa)  > /dev/null 2>&1
