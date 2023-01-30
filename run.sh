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

# Create and run Gennet docker container
echo -e "\nRunning topology generation"
cd gennet-module
docker run --name gennet-container -v ${dir}/config/:/config gennet --config-file /config/${wakurtosis_config_file} --output-dir /config/topology_generated
cd ..

docker rm gennet-container > /dev/null 2>&1

# Delete the enclave just in case
kurtosis enclave rm -f $enclave_name > /dev/null 2>&1

# Create the new enclave and run the simulation
echo -e "\nInitiating enclave "$enclave_name
kurtosis_cmd="kurtosis run --enclave-id ${enclave_name} . '{\"wakurtosis_config_file\" : \"config/${wakurtosis_config_file}\"}' > kurtosisrun_log.txt 2>&1"
eval $kurtosis_cmd
echo -e "Enclave " $enclave_name " is up and running"

# Fetch the WSL service id and display the log of the simulation
wsl_service_id=$(kurtosis enclave inspect wakurtosis 2>/dev/null | grep wsl- | awk '{print $1}')
# kurtosis service logs wakurtosis $wsl_service_id
echo -e "\n--> To see simulation logs run: kurtosis service logs wakurtosis $wsl_service_id <--"

# Fetch the Grafana address & port
grafana_host=$(kurtosis enclave inspect wakurtosis 2>/dev/null | grep grafana- | awk '{print $6}')
echo -e "\n--> Statistics in Grafana server at http://$grafana_host/ <--"

# echo "Output of kurtosis run command written in kurtosisrun_log.txt"

### Wait for WSL to finish

# Get the container suffix for the running service
cid_suffix="$(kurtosis enclave inspect $enclave_name | grep $wsl_service_id | cut -f 1 -d ' ')"

# Construct the fully qualified container name that kurtosis created 
cid="$enclave_name--user-service--$cid_suffix"

# Wait for the container to halt; this will block 
echo "Waiting for simulation to finish ..."
status_code="$(docker container wait $cid)"

# Copy simulation results
docker cp "$cid:/wsl/summary.json" "./"
echo "Simulation results can be found in ./summary.json"

echo "Done."
