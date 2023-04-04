#!/bin/sh

dir=$(pwd)

# Parse arg if any
ARGS1=${1:-"wakurtosis"}
ARGS2=${2:-"config.json"}

# Main .json configuration file
enclave_name=$ARGS1
wakurtosis_config_file=$ARGS2
loglevel="error"

echo "- Enclave name: " $enclave_name
echo "- Configuration file: " $wakurtosis_config_file

# Delete the enclave just in case
echo -e "\nCleaning up Kurtosis environment "$enclave_name
docker container stop cadvisor > /dev/null 2>&1
docker container rm cadvisor > /dev/null 2>&1
kurtosis enclave rm -f $enclave_name > /dev/null 2>&1

# Delete previous logs
echo -e "Deleting previous logs in ${enclave_name}_logs"
rm -rf ./${enclave_name}_logs > /dev/null 2>&1
rm ./kurtosisrun_log.txt > /dev/null 2>&1
rm -f ./monitoring/metrics.json > /dev/null 2>&1
rm -f ./monitoring/*.pdf > /dev/null 2>&1
rm -f ./monitoring/summary.json > /dev/null 2>&1

# Preparing enclave
echo "Preparing enclave..."
kurtosis enclave add --name ${enclave_name}
enclave_preffix="$(kurtosis enclave inspect --full-uuids $enclave_name | grep UUID: | awk '{print $2}')"
echo "Enclave network: "$enclave_preffix

# Get enclave last IP
subnet="$(docker network inspect $enclave_preffix | jq -r '.[].IPAM.Config[0].Subnet')"
echo "Enclave subnetork: $subnet"
last_ip="$(ipcalc $subnet | grep HostMax | awk '{print $2}')"
echo "cAdvisor IP: $last_ip"


# Set up Cadvisor
docker run --volume=/:/rootfs:ro --volume=/var/run:/var/run:rw --volume=/var/lib/docker/:/var/lib/docker:ro --volume=/dev/disk/:/dev/disk:ro --volume=/sys:/sys:ro --volume=/etc/machine-id:/etc/machine-id:ro --publish=8080:8080 --detach=true --name=cadvisor --privileged --device=/dev/kmsg --network $enclave_preffix --ip=$last_ip gcr.io/cadvisor/cadvisor:v0.47.0


# Delete topology
rm -rf ./config/topology_generated > /dev/null 2>&1
# Remove previous logs
rm -rf ./$enclave_name_logs > /dev/null 2>&1

# Run Gennet docker container
echo -e "\nRunning network generation"
docker rm gennet-container > /dev/null 2>&1  # cleanup the old docker if any

docker run --name gennet-container -v ${dir}/config/:/config:ro gennet --config-file /config/${wakurtosis_config_file} --traits-dir /config/traits
err=$?

if [ $err != 0 ]
then
  echo "Gennet failed with error code $err"
  exit
fi

docker cp gennet-container:/gennet/network_data ${dir}/config/topology_generated

docker rm gennet-container > /dev/null 2>&1

# Start process level monitoring (in background, will wait to WSL to be created)
sudo -E python3 ./monitoring/monitor.py &
monitor_pid=$!

# Create the new enclave and run the simulation
jobs=$(cat config/${wakurtosis_config_file} | jq -r ".kurtosis.jobs")

echo -e "\nSetting up the enclave: $enclave_name"
kurtosis_cmd="kurtosis --cli-log-level \"$loglevel\" run --enclave ${enclave_name} . '{\"wakurtosis_config_file\" : \"config/${wakurtosis_config_file}\"}' --parallelism ${jobs} > kurtosisrun_log.txt 2>&1"

START=$(date +%s)
eval $kurtosis_cmd
END1=$(date +%s)
DIFF1=$(( $END1 - $START ))
echo -e "Enclave $enclave_name is up and running: took $DIFF1 secs to setup"

# Extract the WLS service name
wls_service_name=$(kurtosis --cli-log-level $loglevel enclave inspect $enclave_name | grep "\<wls\>" | awk '{print $1}')
echo -e "\n--> To see simulation logs run: kurtosis service logs $enclave_name $wls_service_name <--"


# Fetch the Grafana address & port
grafana_host=$(kurtosis enclave inspect $enclave_name | grep "\<grafana\>" | awk '{print $6}')
echo -e "\n--> Statistics in Grafana server at http://$grafana_host/ <--"

echo "Output of kurtosis run command written in kurtosisrun_log.txt"

# Get the container prefix/uffix for the WLS service
service_name="$(kurtosis --cli-log-level $loglevel  enclave inspect $enclave_name | grep $wls_service_name | awk '{print $2}')"
service_uuid="$(kurtosis --cli-log-level $loglevel  enclave inspect --full-uuids $enclave_name | grep $wls_service_name | awk '{print $1}')"

# Construct the fully qualified container name that kurtosis has created
cid="$service_name--$service_uuid"

# Wait for the container to halt; this will block
echo -e "Waiting for simulation to finish ..."
status_code="$(docker container wait $cid)"

### Logs
kurtosis enclave dump ${enclave_name} ${enclave_name}_logs > /dev/null 2>&1
echo -e "Simulation ended with code $status_code Results in ./${enclave_name}_logs"

END2=$(date +%s)
DIFF2=$(( $END2 - $END1 ))

echo "Simulation took $DIFF1 + $DIFF2 = $(( $END2 - $START)) secs"

# Copy simulation results
docker cp "$cid:/wls/messages.json" "./${enclave_name}_logs"
docker cp "$cid:/wls/network_topology/network_data.json" "./${enclave_name}_logs"

# Wait for metrics to finish
echo -e "Waiting monitoring to finish ..."
wait $monitor_pid

# Run process level analysis
# python3 p_analysis.py 
# echo -e "Analysis results in ./${enclave_name}_logs"

# Stop and delete the enclave
echo "Stopping and destrying enclave $enclave_name ..."
kurtosis enclave stop $enclave_name > /dev/null 2>&1
kurtosis enclave rm -f $enclave_name > /dev/null 2>&1

echo "Done."
