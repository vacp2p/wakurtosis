#!/bin/sh

dir=$(pwd)

# Parse arg if any
ARGS1=${1:-"wakurtosis"}
ARGS2=${2:-"./config/config.json"}
ARGS3=${3:-"gennet-module/config/gennet.yml"}

# Main .json configuration file
enclave_name=$ARGS1
kurtosis_config_file=$ARGS2
gennet_config_file=$ARGS3

echo "- Enclave name: " enclave_name
echo "- Configuration file: " kurtosis_config_file
echo "- Topology configuration: " gennet_config_file

# Create and run gennet docker container
echo -e "\nRunning topology generation with configuration:"
cd gennet-module
docker run --name gennet-container -v ${dir}/gennet-module/config:/gennet/config gennet
cd ..

# Move output from gennet to config folder so kurtosis will use it
echo -e "\nReplacing new topology data..."
mv -f gennet-module/config/topology_generated/network_data.json config/network_topology/
mv -f gennet-module/config/topology_generated/*.toml config/waku_config_files

docker rm gennet-container > /dev/null 2>&1

# Delete the enclave just in case
kurtosis enclave rm -f $enclave_name > /dev/null 2>&1

# Create the new enclave and run the simulation
echo -e "\nInitiating enclave " $enclave_name
kurtosis_cmd="kurtosis run --enclave-id ${enclave_name} . '{\"kurtosis_config_file\" : \"config/${kurtosis_config_file}\"}' > kurtosis_log.txt 2>&1"
eval $kurtosis_cmd
echo -e "Enclave " $enclave_name " is up and running"

# Fetch the WSL service id and display the log of the simulation
wsl_service_id=$(kurtosis enclave inspect wakurtosis 2>/dev/null | grep wsl- | awk '{print $1}')
# kurtosis service logs wakurtosis $wsl_service_id
echo -e "\n--> To see simulation logs run: kurtosis service logs wakurtosis $wsl_service_id <--"

# Fetch the Grafana address & port
grafana_host=$(kurtosis enclave inspect wakurtosis 2>/dev/null | grep grafana- | awk '{print $6}')
echo -e "\n--> Statistics in Grafana server at http://$grafana_host/ <--"