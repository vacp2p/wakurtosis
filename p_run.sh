#!/bin/sh

dir=$(pwd)

# Parse arg if any
ARGS1=${1:-"wakurtosis"}
ARGS2=${2:-"config.json"}

# Main .json configuration file
enclave_name=$ARGS1
wakurtosis_config_file=$ARGS2

echo "- Enclave name: " $enclave_name
echo "- Configuration file: " $wakurtosis_config_file

# Cleanup
echo -e "\nCleaning up Kurtosis environment "$enclave_name
kurtosis enclave rm -f $enclave_name > /dev/null 2>&1

echo -e "\Deleting previous logs in ${enclave_name}_logs"
sudo rm -rf ./${enclave_name}_logs > /dev/null 2>&1
sudo rm -f ./kurtosisrun_log.txt > /dev/null 2>&1
sudo rm -f ./monitoring/metrics.json > /dev/null 2>&1
sudo rm -f ./monitoring/*.pdf > /dev/null 2>&1
sudo rm -f ./monitoring/summary.json > /dev/null 2>&1

sudo rm -rf ./config/topology_generated > /dev/null 2>&1

# Preparing enclave
echo "Preparing enclave..."
kurtosis enclave add --name ${enclave_name}
enclave_preffix="$(kurtosis enclave inspect --full-uuids $enclave_name | grep UUID: | awk '{print $2}')"
echo "Enclave network: "$enclave_preffix

# Create and run Gennet docker container
echo -e "\nRunning network generation"
docker rm gennet-container > /dev/null 2>&1
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

# Start process level monitoring (in background, will wait to WSL to be created)
sudo -E python3 ./monitoring/monitor.py &
monitor_pid=$!

# Create the new enclave and run the simulation
jobs=$(cat config/${wakurtosis_config_file} | jq -r ".kurtosis.jobs")

echo -e "\nInitiating enclave "$enclave_name
kurtosis_cmd="kurtosis run --enclave-id ${enclave_name} . '{\"wakurtosis_config_file\" : \"config/${wakurtosis_config_file}\"}' --parallelism ${jobs} > kurtosisrun_log.txt 2>&1"
eval $kurtosis_cmd
echo -e "Enclave " $enclave_name " is up and running"

# Fetch the WSL service id and display the log of the simulation
wsl_service_name=$(kurtosis enclave inspect $enclave_name 2>/dev/null | grep wsl | awk '{print $1}')

# Fetch the Grafana address & port
grafana_host=$(kurtosis enclave inspect $enclave_name | grep grafana | awk '{print $6}')
echo -e "\n--> Statistics in Grafana server at http://$grafana_host/ <--"

echo "Output of kurtosis run command written in kurtosisrun_log.txt"

# Get the container suffix for the running service
enclave_preffix="$(kurtosis enclave inspect --full-uuids $enclave_name | grep UUID: | awk '{print $2}')"
cid_suffix="$(kurtosis enclave inspect --full-uuids $enclave_name | grep $wsl_service_name | cut -f 1 -d ' ')"

# Construct the fully qualified container name that kurtosis created
cid="$enclave_preffix--user-service--$cid_suffix"

# Wait for the container to halt; this will block
echo -e "Waiting for simulation to finish ..."
status_code="$(docker container wait $cid)"

### Logs
kurtosis enclave dump ${enclave_name} ${enclave_name}_logs > /dev/null 2>&1
echo -e "Simulation ended with code $status_code Results in ./${enclave_name}_logs"

# Copy simulation results
echo -e "Copying messages ..."
docker cp "$cid:/wsl/messages.json" "./${enclave_name}_logs"

# Wait for metrics to finish
echo -e "Waiting monitoring to finish ..."
wait $monitor_pid

# Run process level analysis
python3 p_analysis.py 
echo -e "Analysis results in ./${enclave_name}_logs"

# Stop and delete the enclave
echo "Stopping and destrying enclave $enclave_name ..."
kurtosis enclave stop $enclave_name > /dev/null 2>&1
kurtosis enclave rm -f $enclave_name > /dev/null 2>&1

echo "Done."
