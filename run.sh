#!/bin/sh

dir=$(pwd)

# Set up Cadvisor
docker run --volume=/:/rootfs:ro --volume=/var/run:/var/run:rw --volume=/var/lib/docker/:/var/lib/docker:ro --volume=/dev/disk/:/dev/disk:ro --volume=/sys:/sys:ro --volume=/etc/machine-id:/etc/machine-id:ro --publish=8080:8080 --detach=true --name=cadvisor --privileged --device=/dev/kmsg gcr.io/cadvisor/cadvisor


# Parse arg if any
ARGS1=${1:-"wakurtosis"}
ARGS2=${2:-"config.json"}

# Main .json configuration file
enclave_name=$ARGS1
wakurtosis_config_file=$ARGS2
loglevel="error"

echo "- Enclave name: " $enclave_name
echo "- Configuration file: " $wakurtosis_config_file

# Run Gennet 
echo -e "\nRunning Gennet"
docker rm gennet-container > /dev/null 2>&1  # cleanup the old docker if any
cd gennet-module
docker run --name gennet-container -v ${dir}/config/:/config gennet --config-file /config/${wakurtosis_config_file} --output-dir /config/topology_generated
err=$?
cd ..

if [ $err != 0 ]
then
  echo "Gennet failed with error code $err"
  exit
fi

docker rm gennet-container > /dev/null 2>&1

# Delete the enclave just in case
kurtosis enclave rm -f $enclave_name > /dev/null 2>&1

# Create a new enclave and run the simulation
jobs=$(cat config/${wakurtosis_config_file} | jq -r ".kurtosis.jobs")

echo -e "\nSetting up the enclave: $enclave_name"
kurtosis_cmd="kurtosis --cli-log-level \"$loglevel\" run --enclave-id ${enclave_name} . '{\"wakurtosis_config_file\" : \"config/${wakurtosis_config_file}\"}' --parallelism ${jobs} > kurtosisrun_log.txt 2>&1"

START=$(date +%s)
eval $kurtosis_cmd
END1=$(date +%s)
DIFF1=$(( $END1 - $START ))
echo -e "Enclave $enclave_name is up and running: took $DIFF1 secs to setup"

# Extract the WLS service name
wls_service_name=$(kurtosis --cli-log-level $loglevel enclave inspect $enclave_name | grep wls | awk '{print $1}')
# kurtosis service logs $enclave_name $wls_service_name
echo -e "\n--> To see simulation logs run: kurtosis service logs $enclave_name $wls_service_name <--"

# Extract the Grafana host:port
# TODO: needs fixing
grafana_host=$(kurtosis --cli-log-level $loglevel enclave inspect $enclave_name | grep grafana | awk '{print $6}')
echo -e "\n--> Statistics in Grafana server at http://$grafana_host/ <--"

# echo "Output of kurtosis run command written in kurtosisrun_log.txt"

### Wait for WLS to finish

# Get the container prefix/uffix for the WLS service
enclave_prefix="$(kurtosis --cli-log-level $loglevel  enclave inspect --full-uuids $enclave_name | grep UUID: | awk '{print $2}')"
cid_suffix="$(kurtosis --cli-log-level $loglevel  enclave inspect --full-uuids $enclave_name | grep $wls_service_name | cut -f 1 -d ' ')"

# Construct the fully qualified container name that kurtosis has created
cid="$enclave_prefix--user-service--$cid_suffix"

# Wait for the container to halt; this will block
echo "Waiting for simulation to finish ..."
status_code="$(docker container wait $cid)"

END2=$(date +%s)
DIFF2=$(( $END2 - $END1 ))

echo "Simulation took $DIFF1 + $DIFF2 = $(( $END2 - $START)) secs"
# Copy simulation results
#docker cp "$cid:/wls/summary.json" "./"
#echo "Simulation ended with code $status_code Results in ./summary.json"

# Stop and delete the enclave
# kurtosis enclave stop $enclave_name > /dev/null 2>&1
# kurtosis enclave rm -f $enclave_name > /dev/null 2>&1
# echo "Enclave $enclave_name stopped and deleted."

echo "Done."
