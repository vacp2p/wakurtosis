#!/bin/sh

# Parse arg if any
ARGS1=${1:-"./config/config.json"}
ARGS2=${2:-"gennet-module/config/gennet.yml"}
echo $ARGS1
echo $ARGS2

# Main .json configuration file
kurtosis_config_file=$ARGS1
gennet_config_file=$ARGS2


# Create and run gennet docker container
cd gennet-module
docker run --name gennet -v $PWD/gennet-module/:/gennet gennet
cd ..

# Move output from gennet to config folder so kurtosis will use it
mv gennet-module/topology/network_data.json config/network_topology/
mv gennet-module/topology/*.toml config/waku_config_files

docker rm gennet
docker volume rm $PWD/gennet-module/

# Delete the enclave 
kurtosis enclave rm -f $enclave_name

# Create the new enclave and run the simulation
kurtosis_cmd="kurtosis run --enclave-id ${enclave_name} . '{\"kurtosis_config_file\" : \"config/${kurtosis_config_file}\"}'"
eval $kurtosis_cmd

# Fetch the WSL service id and display the log of the simulation
wsl_service_id=$(kurtosis enclave inspect wakurtosis | grep wsl- | awk '{print $1}')
kurtosis service logs wakurtosis $wsl_service_id
echo "--> To see simulation logs run: kurtosis service logs wakurtosis $wsl_service_id <--"

# Fetch the Grafana address & port
grafana_host=$(kurtosis enclave inspect wakurtosis | grep grafana- | awk '{print $6}')
echo "--> Statistics in Grafana server at http://$grafana_host/ <--"